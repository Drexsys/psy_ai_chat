import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
from db import DB_connection

db = DB_connection()

MAX_SCORE = 120

def plot_radar(df_llm, truth, traits, username):
    mean_scores = df_llm.groupby('model')[traits].mean()
    N = len(traits)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    truth_vals = [truth[t] for t in traits]
    truth_vals += truth_vals[:1]

    ax.plot(angles, truth_vals, linewidth=3, linestyle='--', color='black', label='Реальний Тест (Еталон)')
    ax.fill(angles, truth_vals, color='black', alpha=0.1)

    for index, row in mean_scores.iterrows():
        vals = row.tolist()
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2, label=f'{index} (Середнє)')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([t.capitalize() for t in traits])
    ax.set_ylim(0, MAX_SCORE)

    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    # Додано ім'я користувача до назви
    plt.title(f"Усереднений профіль OCEAN: {username} (Бали)", size=14, pad=20)
    plt.tight_layout()
    plt.show()


def plot_stability(df_llm, username):
    if 'mean_error' not in df_llm.columns:
        print("Помилка: 'mean_error' не розраховано.")
        return

    plt.figure(figsize=(10, 6))
    sns.boxplot(
        x='model',
        y='mean_error',
        data=df_llm,
        hue='model',
        palette="Set2",
        legend=False
    )
    sns.swarmplot(x='model', y='mean_error', data=df_llm, color=".25")

    plt.title(f"Стабільність оцінок (%): {username}", size=14)
    plt.ylabel("Середня абсолютна похибка (%)")
    plt.xlabel("Модель ШІ")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    from matplotlib.ticker import PercentFormatter
    plt.gca().yaxis.set_major_formatter(PercentFormatter())

    plt.tight_layout()
    plt.show()


def print_analytics(df_llm, label="", is_global=False):
    print(f"\n--- АНАЛІТИКА ТОЧНОСТІ МОДЕЛЕЙ (%) {label} ---")

    if 'mean_error' not in df_llm.columns:
        print("Немає даних для аналітики.")
        return

    if is_global:
        # ПРАВИЛЬНИЙ РОЗРАХУНОК ДЛЯ ЗАГАЛЬНОЇ ТАБЛИЦІ:
        # 1. Рахуємо метрики для кожного користувача окремо
        user_metrics = df_llm.groupby(['model', 'username'])['mean_error'].agg(['mean', 'std']).reset_index()

        # 2. Беремо середнє від цих метрик по моделях
        # Це дасть "Середню похибку серед користувачів" та "Середню стабільність моделі"
        summary = user_metrics.groupby('model').agg({
            'mean': 'mean',
            'std': 'mean'
        }).reset_index()

        summary.rename(columns={'mean': 'Сер. похибка (Mean of Means, %)',
                                'std': 'Сер. стабільність (Mean of Std, %)'}, inplace=True)
    else:
        # Для окремого користувача залишаємо як було
        summary = df_llm.groupby('model')['mean_error'].agg(['mean', 'std']).reset_index()
        summary.rename(columns={'mean': 'Сер. похибка (%)', 'std': 'Стабільність (std %)'}, inplace=True)

    print(summary.to_markdown(index=False))

def parse_data(user_id):
    db.cursor.execute("SELECT * FROM chats_res WHERE user_id = %s;", (user_id,))
    chats = db.cursor.fetchall()
    temp = []
    for result in chats:
        db.cursor.execute("SELECT name FROM models WHERE id = %s;", (result[2],))
        model_name = db.cursor.fetchone()[0]
        db.cursor.execute("SELECT * FROM res WHERE id = %s;", (result[3],))
        res = db.cursor.fetchone()
        temp.append({
            'model': model_name,
            'openness': res[1],
            'conscientiousness': res[2],
            'extraversion': res[3],
            'agreeableness': res[4],
            'neuroticism': res[5]
        })
    return temp


def get_true_data(user_id):
    db.cursor.execute("SELECT res_id FROM true_res WHERE user_id = %s;", (user_id,))
    res_id_row = db.cursor.fetchone()
    if not res_id_row: return None
    db.cursor.execute("SELECT * FROM res WHERE id = %s;", (res_id_row[0],))
    res = db.cursor.fetchone()
    return {
        'model': 'Real Test',
        'openness': res[1],
        'conscientiousness': res[2],
        'extraversion': res[3],
        'agreeableness': res[4],
        'neuroticism': res[5]
    }

def main():
    db.cursor.execute("SELECT id, username FROM users;")
    users = db.cursor.fetchall()
    all_users_data = []

    for user in users:
        u_id, u_name = user[0], user[1]
        ground_truth = get_true_data(u_id)
        llm_data_raw = parse_data(u_id)

        if not ground_truth or not llm_data_raw:
            continue

        llm_data = pd.DataFrame(llm_data_raw)
        llm_data['username'] = u_name

        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        for trait in traits:
            llm_data[f'error_{trait}'] = (abs(llm_data[trait] - ground_truth[trait]) / MAX_SCORE) * 100

        error_cols = [f'error_{t}' for t in traits]
        llm_data['mean_error'] = llm_data[error_cols].mean(axis=1)
        all_users_data.append(llm_data)

        print_analytics(llm_data, label=f"КОРИСТУВАЧ: {u_name}", is_global=False)

        plot_radar(llm_data, ground_truth, traits, u_name)
        plot_stability(llm_data, u_name)

    if all_users_data:
        final_df = pd.concat(all_users_data, ignore_index=True)
        print("\n" + "=" * 60)
        print("ПРАВИЛЬНІ ЗАГАЛЬНІ РЕЗУЛЬТАТИ (АГРЕГОВАНІ ПО КОРИСТУВАЧАХ)")
        print("=" * 60)
        print_analytics(final_df, label="ЗАГАЛОМ", is_global=True)

if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()