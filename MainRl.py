import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import talib  # type: ignore
import pickle

# from stable_baselines3.common.logger import configure
# from stable_baselines3.common.env_checker import check_env
import random


class TradingEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, data_file, start_date, end_date):
        super(TradingEnv, self).__init__()

        self.data_file = data_file
        self.start_date = start_date
        self.end_date = end_date

        self.tradingClass = TradingClass()
        error, self.guiParams = self.tradingClass.LoadSettings(self)
        self.guiParams.StartDt = start_date
        self.guiParams.EndDt = end_date
        self.df = data_file
        self.df = self.df.loc[start_date:end_date]
        self.OpenTradesCount = 0

        self.floats_Rebuy1stPercent = [round(x * 0.1, 1) for x in range(1, 21)]
        self.floats_RebuyPercent = [round(x * 0.01, 10) for x in range(1, 21)]
        self.floats_TakeProfitPercent = [round(x * 0.01, 10) for x in range(1, 21)]

        self.action_space = spaces.MultiDiscrete([20, 20, 20])

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(self.df.columns) + 11, 60),
            dtype=np.float64,
        )
        self.current_step = 0

        self.past_actions = []
        self.past_rewards = []

        self.additional_features_history = []

    def _next_observation(self):
        self.window_size = 60  # last n steps
        end = self.current_step
        start = max(0, end - self.window_size)
        obs = self.df.iloc[start:end].T.values

        if obs.shape[1] < self.window_size:
            pad_width = self.window_size - obs.shape[1]
            obs = np.pad(obs, ((0, 0), (pad_width, 0)), mode="constant", constant_values=0)

        past_actions_rewards = np.zeros((4, self.window_size))
        num_past_steps = len(self.past_actions)
        if num_past_steps > 0:
            past_actions_array = np.array(self.past_actions[-self.window_size :])
            past_rewards_array = np.array(self.past_rewards[-self.window_size :])

            action_reward_data = np.hstack((past_actions_array, past_rewards_array.reshape(-1, 1))).T
            past_actions_rewards[:, -num_past_steps:] = action_reward_data

        obs = np.vstack((obs, past_actions_rewards))

        additional_features = [
            self.tradingClass.InvestCount,
            self.tradingClass.Account.Balance,
            self.tradingClass.Account.UnrealizedNetProfit,
            self.tradingClass.AvgOpenDurationSum[0],
            self.tradingClass.AvgPrice,
            self.tradingClass.ClusterProfit,
            self.tradingClass.IsLong,
        ]

        self.additional_features_history.append(additional_features)
        if len(self.additional_features_history) > self.window_size:
            self.additional_features_history.pop(0)

        additional_features_array = np.array(self.additional_features_history).T

        if additional_features_array.shape[1] < self.window_size:
            pad_width = self.window_size - additional_features_array.shape[1]
            additional_features_array = np.pad(
                additional_features_array,
                ((0, 0), (pad_width, 0)),
                mode="constant",
                constant_values=0,
            )

        obs = np.vstack((obs, additional_features_array))
        return obs

    def reset(self, seed=None, **kwargs):
        np.random.seed(seed)
        super().reset(seed=seed)

        self.current_step = 0

        self.tradingClass = TradingClass()
        error, self.guiParams = self.tradingClass.LoadSettings(self)
        self.guiParams.StartDt = self.start_date
        self.guiParams.EndDt = self.end_date
        self.df = self.data_file
        self.df = self.df.loc[self.start_date : self.end_date]
        self.OpenTradesCount = 0

        self.tradingClass.IsTrain = self.IsTrain
        self.tradingClass.PreStart(self.guiParams)
        self.tradingClass.OnStart()

        self.past_actions = []
        self.past_rewards = []

        self.additional_features_history = []

        obs = self._next_observation()

        return obs, {}

    def step(self, action):
        self.tradingClass.BinParameters.Rebuy1stPercent = self.floats_Rebuy1stPercent[action[0]]
        self.tradingClass.BinParameters.RebuyPercent = self.floats_RebuyPercent[action[1]]
        self.tradingClass.BinParameters.TakeProfitPercent = self.floats_TakeProfitPercent[action[2]]

        if self.current_step >= len(self.df):
            terminated = True
        else:
            terminated = False
            self.tradingClass.Tick()  ############## do one tick ##########

        truncated = False

        reward = self.tradingClass.calculate_reward(self.tradingClass)
        info = {}

        self.past_actions.append(
            [
                self.tradingClass.BinParameters.Rebuy1stPercent,
                self.tradingClass.BinParameters.RebuyPercent,
                self.tradingClass.BinParameters.TakeProfitPercent,
            ]
        )
        self.past_rewards.append(reward)

        self.current_step += 1

        if not terminated:
            obs = self._next_observation()
        else:
            obs = None

        # if 0 != reward:
        #    pass

        # Update previous time (time of last tick)
        if self.tradingClass.PrevTime.date() != self.tradingClass.Time.date():
            print(self.tradingClass.Time.date())

        self.tradingClass.PrevTime = self.tradingClass.Time
        return obs, reward, terminated, truncated, info

    def render(self, mode="human"):
        pass


def main():
    def get_model(seed=None, train=False):
        model = PPO(
            "MlpPolicy",
            train_env,
            # tensorboard_log=log_dir,
            verbose=1,
            learning_rate=0.00025,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.15,
            batch_size=64,
            n_steps=2048,
            seed=seed,
        )

        train_env.IsTrain = test_env.IsTrain = train
        if train:
            print("UseNewlyTrainedModel")
            model.learn(total_timesteps=len(df_train))
            model.save("ppo_trading_model_2y")
        else:
            print("UseStoredTrainedModel")
            model.load("ppo_trading_model_2y")

        return model

    def run_test(env, action_strategy, i, trained_model):
        obs, _ = env.reset(seed=i)

        history = []
        terminated = False
        total_rewards = 0
        while not terminated:
            if action_strategy == "model":
                action, _states = trained_model.predict(obs, deterministic=True)
            elif action_strategy == "fixed":
                action = np.array([10, 9, 8])
            elif action_strategy == "random":
                action = env.action_space.sample()
            else:
                raise ValueError("Invalid action strategy")

            ########### do one step ################
            obs, rewards, terminated, truncated, info = env.step(action)
            total_rewards += rewards
            env.render()

            history.append(
                [
                    env.tradingClass.Time.strftime("%d-%m-%Y %H:%M:%S"),
                    env.tradingClass.Account.Balance,
                    env.tradingClass.MaxEquityDrawdownValue[0],
                    env.tradingClass.Calmar,
                    env.tradingClass.ClusterCount,
                    env.tradingClass.InvestCount,
                    env.tradingClass.BinParameters.Rebuy1stPercent,
                    env.tradingClass.BinParameters.RebuyPercent,
                    env.tradingClass.BinParameters.TakeProfitPercent,
                ]
            )

            if terminated:
                df_history = pd.DataFrame(
                    history,
                    columns=[
                        "Time",
                        "Account Balance",
                        "Max Equity Drawdown",
                        "Calmar",
                        "Cluster Count",
                        "Invest Count",
                        "Rebuy 1st Percent",
                        "Rebuy Percent",
                        "Take Profit Percent",
                    ],
                )
                return (
                    env.tradingClass.Account.Balance,
                    env.tradingClass.MaxEquityDrawdownValue[0],
                    env.tradingClass.Calmar,
                    df_history,
                )

    def evaluate_strategy(env, action_strategy, num_runs, trained_model):
        account_balance_results = []
        max_draw_down_results = []
        calmar_results = []
        history_results = []

        for i in range(num_runs):
            result = run_test(env, action_strategy, i, trained_model)
            account_balance_results.append(result[0])
            max_draw_down_results.append(result[1])
            calmar_results.append(result[2])
            history_results.append(result[3])

        account_balance_mean = np.mean(account_balance_results)
        account_balance_std = np.std(account_balance_results)
        max_draw_down_mean = np.mean(max_draw_down_results)
        max_draw_down_std = np.std(max_draw_down_results)
        calmar_mean = np.mean(calmar_results)
        calmar_std = np.std(calmar_results)

        return (
            account_balance_mean,
            account_balance_std,
            max_draw_down_mean,
            max_draw_down_std,
            calmar_mean,
            calmar_std,
            history_results,
        )

    df_full = pd.read_pickle("combined_forex_data.pkl")

    time_period = 100
    nb_dev_up = 2
    nb_dev_dn = 2

    upperband, middleband, lowerband = talib.BBANDS(
        df_full["Close"].shift(1),
        timeperiod=time_period,
        nbdevup=nb_dev_up,
        nbdevdn=nb_dev_dn,
        matype=0,  # Simple Moving Average
    )

    df_full["Bollinger Upper"] = upperband
    df_full["Bollinger Middle"] = middleband
    df_full["Bollinger Lower"] = lowerband

    df_full = df_full.shift(1)

    df_full = df_full[["Bollinger Upper", "Bollinger Middle", "Bollinger Lower"]].copy()

    start_date_train = "2023-01-01"
    end_date_train = "2023-12-31"
    df_train = df_full.loc[start_date_train:end_date_train]
    train_env = TradingEnv(data_file=df_train, start_date=start_date_train, end_date=end_date_train)

    # check_env(train_env)
    # log_dir = "./tensorboard_logs/"
    # os.makedirs(log_dir, exist_ok=True)
    # configure(log_dir, ["stdout", "tensorboard"])

    start_date_test = "2024-01-01"
    end_date_test = "2024-12-31"
    df_test = df_full.loc[start_date_test:end_date_test]

    test_env = TradingEnv(data_file=df_test, start_date=start_date_test, end_date=end_date_test)

    # isTrain = True
    isTrain = False
    trained_model = get_model(seed=random.randint(1, 10), train=isTrain)

    M = 10
    print("\nRunning fixed action strategy")
    fixed_results = evaluate_strategy(test_env, "fixed", 1, trained_model)

    print("\nRunning random action strategy")
    random_results = evaluate_strategy(test_env, "random", M, trained_model)

    print("Running model action strategy")
    model_results = evaluate_strategy(test_env, "model", M, trained_model)

    results_df = pd.DataFrame(
        {
            "Strategy": ["Model", "Fixed", "Random"],
            "Account Balance Mean": [
                model_results[0],
                fixed_results[0],
                random_results[0],
            ],
            "Account Balance Std": [
                model_results[1],
                fixed_results[1],
                random_results[1],
            ],
            "Max Drawdown Mean": [
                model_results[2],
                fixed_results[2],
                random_results[2],
            ],
            "Max Drawdown  Std": [
                model_results[3],
                fixed_results[3],
                random_results[3],
            ],
            "Calmar Mean": [model_results[4], fixed_results[4], random_results[4]],
            "Calmar Std": [model_results[5], fixed_results[5], random_results[5]],
        }
    )

    history_dfs = dict(Model=model_results[6], Fixed=fixed_results[6], Random=random_results[6])

    print("\nComparison of Results:")
    print(results_df)

    results_df.to_pickle("trading_strategy_results.pkl")
    with open("trading_strategy_history.pkl", "wb") as f:
        pickle.dump(history_dfs, f)

    print("done")


if __name__ == "__main__":
    main()
