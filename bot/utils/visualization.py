import io
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, Optional

from bot.utils.helpers import wrap_text, questions_map
from bot.db.database import get_question_answers


def generate_pie_chart(question_id):
    """Generate a pie chart for a specific question and return image as bytes"""
    if question_id not in questions_map:
        return None, None  # If question not found

    # Get question info
    question_info = questions_map[question_id]
    question_text = question_info["question"]
    is_multiple_choice = question_info["multiple_choice"]

    # Get answers from SQLAlchemy database
    answers_data = get_question_answers(question_id)

    if not answers_data:
        return None, None  # If no answers

    # Process answers
    all_answers = []

    for answer in answers_data:
        answer_text = answer["answer_text"]
        if answer_text:
            if is_multiple_choice and " | " in answer_text:
                split_answers = answer_text.split(" | ")
                all_answers.extend([a.strip() for a in split_answers])
            else:
                all_answers.append(answer_text.strip())

    if not all_answers:
        return None, None  # If no valid answers after processing

    # Count answer frequency
    answer_counts = pd.Series(all_answers).value_counts()

    # Create figure
    plt.figure(figsize=(8, 6))

    # Create subplot
    ax = plt.subplot(111)

    # Use color blind friendly color palette
    colors = plt.cm.tab10.colors[:len(answer_counts)]

    # Get the original labels
    original_labels = list(answer_counts.index)

    # Wrap labels for better display
    wrapped_labels = [wrap_text(label, max_width=15) for label in original_labels]

    # Format question text with wrapping
    wrapped_question = wrap_text(question_text, max_width=40)

    # Create pie chart with wrapped labels
    wedges, texts, autotexts = ax.pie(
        answer_counts.values,
        labels=wrapped_labels,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        textprops={'fontsize': 9}
    )

    # Improve text properties for better readability
    plt.setp(texts, fontsize=8)
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    # Add title with wrapped question text
    ax.set_title(f"Питання {question_id}:\n{wrapped_question}", fontsize=10, pad=15)

    # Make sure the pie chart is a circle
    ax.axis('equal')

    # Save chart to memory buffer with higher DPI for better quality
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=120, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    # Prepare text data for return
    total_responses = sum(answer_counts.values)
    color_data_text = ""

    for answer, count in answer_counts.items():
        percentage = (count / total_responses) * 100
        color_data_text += f"{answer} - {count} відповідей ({percentage:.1f}%)\n"

    return buffer, color_data_text


def generate_survey_stats_chart() -> Tuple[Optional[io.BytesIO], Optional[str]]:
    """Generate a chart showing overall survey statistics"""
    from bot.db.database import get_survey_stats

    # Get survey statistics
    stats = get_survey_stats()

    if stats["total_users"] == 0:
        return None, None  # No data to visualize

    # Create figure
    plt.figure(figsize=(8, 6))

    # Create subplot for completion rate
    ax1 = plt.subplot(121)

    # Create a pie chart for completion rate
    completion_labels = ['Завершено', 'Не завершено']
    completion_values = [stats["completed_surveys"],
                         stats["total_users"] - stats["completed_surveys"]]
    completion_colors = ['#4CAF50', '#F44336']

    ax1.pie(
        completion_values,
        labels=completion_labels,
        autopct='%1.1f%%',
        colors=completion_colors,
        startangle=90,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        textprops={'fontsize': 9}
    )

    ax1.set_title("Відсоток завершення опитування", fontsize=10)

    # Create subplot for statistics
    ax2 = plt.subplot(122)

    # Create a bar chart for survey statistics
    stat_labels = ['Всього користувачів', 'Завершених опитувань', 'Всього відповідей']
    stat_values = [stats["total_users"], stats["completed_surveys"], stats["total_answers"]]

    bars = ax2.bar(
        stat_labels,
        stat_values,
        color=['#2196F3', '#4CAF50', '#FFC107']
    )

    # Add labels to the bars
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(
            f'{height}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha='center',
            va='bottom'
        )

    ax2.set_title("Статистика опитування", fontsize=10)
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Save chart to memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=120, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    # Prepare text data
    stats_text = (
        f"📊 Статистика опитування:\n\n"
        f"Всього користувачів: {stats['total_users']}\n"
        f"Завершених опитувань: {stats['completed_surveys']}\n"
        f"Відсоток завершення: {stats['completion_rate']:.1f}%\n"
        f"Всього відповідей: {stats['total_answers']}\n"
    )

    return buffer, stats_text