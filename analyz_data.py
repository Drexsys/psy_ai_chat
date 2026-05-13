import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
from db import DB_connection

db = DB_connection()

def plot_radar(df_llm, truth, traits):
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
    ax.set_ylim(0, 100)

    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.title("Усереднений профіль OCEAN: ШІ проти Еталону", size=14, pad=20)
    plt.tight_layout()
    plt.show()

def plot_stability(df_llm):
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

    plt.title("Стабільність оцінок: Розподіл похибки (MAE)", size=14)
    plt.ylabel("Середня абсолютна похибка (бали)")
    plt.xlabel("Модель ШІ")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

def print_analytics(df_llm):
    print("\n--- АНАЛІТИКА ТОЧНОСТІ МОДЕЛЕЙ ---")
    if 'mean_error' in df_llm.columns:
        summary = df_llm.groupby('model')['mean_error'].agg(['mean', 'std']).reset_index()
        summary.rename(columns={'mean': 'Сер. похибка', 'std': 'Стабільність (std)'}, inplace=True)
        print(summary.to_markdown(index=False))
    else:
        print("Немає даних для аналітики (mean_error відсутня).")

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

    if not res_id_row:
        return None

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

    for user in users:
        print(f"\nОбробка даних для користувача: {user[1]} (ID: {user[0]})")

        ground_truth = get_true_data(user[0])
        llm_data_raw = parse_data(user[0])

        if not ground_truth:
            print(f"Еталонний тест для {user[1]} відсутній.")
            continue

        if not llm_data_raw:
            print(f"Дані чатів для {user[1]} відсутні.")
            continue

        llm_data = pd.DataFrame(llm_data_raw)

        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        for trait in traits:
            llm_data[f'error_{trait}'] = abs(llm_data[trait] - ground_truth[trait])

        error_cols = [f'error_{t}' for t in traits]
        llm_data['mean_error'] = llm_data[error_cols].mean(axis=1)

        plot_radar(llm_data, ground_truth, traits)
        plot_stability(llm_data)
        print_analytics(llm_data)

if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()
