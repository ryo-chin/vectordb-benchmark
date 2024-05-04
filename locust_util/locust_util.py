import csv
import datetime
import os
from locust.env import Environment

def save_stats_csv(environment: Environment, filename_prefix: str) -> None:
    stats = environment.stats.total
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    num_users = environment.parsed_options.num_users
    os.makedirs("benchmark_results", exist_ok=True)  # 結果を保存するディレクトリ
    filepath = os.path.join("benchmark_results", f"{filename_prefix}_{num_users}users_{current_time}.csv")
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # CSVのヘッダー
        writer.writerow(["p50", "p75", "p90", "p95", "max", "last_rps", "total_rps"])
        writer.writerow(
            [
                stats.get_response_time_percentile(0.5),  # p50
                stats.get_response_time_percentile(0.75),  # p75
                stats.get_response_time_percentile(0.90),  # p90
                stats.get_response_time_percentile(0.95),  # p95
                stats.max_response_time,  # 最大応答時間
                stats.current_rps,  # 現在のRPS
                stats.total_rps,  # 累計RPS
            ]
        )
    print(f"Results saved to {filepath}")