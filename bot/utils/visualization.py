import io
import pandas as pd
import matplotlib.pyplot as plt

from bot.configs import answers_sheet
from bot.utils.helpers import wrap_text, questions_map


def generate_pie_chart(question_id):
    """Generate a pie chart for a specific question and return image as bytes"""
    # Get data from Google Sheets
    data = answers_sheet.get_all_records()
    df = pd.DataFrame(data)

    if question_id not in questions_map:
        return None, None  # If question not found

    question_info = questions_map[question_id]
    question_text = question_info["question"]
    is_multiple_choice = question_info["multiple_choice"]

    filtered_df = df[df['Питання ID'] == question_id]

    if filtered_df.empty:
        return None, None  # If no answers

    # Process answers
    all_answers = []

    for answer in filtered_df['Обраний варіант']:
        if isinstance(answer, str):
            if is_multiple_choice:
                split_answers = answer.split('|')  # If multiple choice question
                all_answers.extend([a.strip() for a in split_answers])
            else:
                all_answers.append(answer.strip())
        else:
            all_answers.append(str(answer).strip())  # Process numeric values

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