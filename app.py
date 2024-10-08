from collections import defaultdict

import jsonlines
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "1aa49uoqij_ahkdvbGtki3lurq"
app.config["APPLICATION_ROOT"] = "/llmjunkevaluator"

# Path to the JSONL file
DATA_FILE = "data.jsonl"


def convert_to_annotation(data):
    print(data)
    # Create a defaultdict where each key will hold a list
    annotation_dict = defaultdict(list)

    # Loop through the input data (list of tuples)
    for key, value in data:
        # Split the key to extract the indices
        _, i, j = key.split("_")
        i = int(i)  # Convert the first index to an integer

        # Append the value to the corresponding list in the dictionary
        annotation_dict[i].append(value)

    # Convert the defaultdict to a regular list of lists
    annotation = [annotation_dict[i] for i in sorted(annotation_dict)]

    return annotation


def load_data():
    """Load data from the JSONL file and return it as a list of dictionaries."""
    data = []
    with jsonlines.open(DATA_FILE, mode="r") as reader:
        for obj in reader:
            data.append(obj)
    return data


def save_data(data):
    """Save the updated data to the JSONL file."""
    with jsonlines.open(DATA_FILE, mode="w") as writer:
        writer.write_all(data)


def get_next_unannotated_row(annotator, data):
    for index, row in enumerate(data):
        if f"annotator_{annotator}" not in row:
            return index
    return index


@app.route("/", methods=["GET", "POST"])
def enter_name():
    if "annotator" in session:
        return redirect(url_for("annotate"))
    if request.method == "POST":
        annotator_name = request.form.get("annotator")
        if annotator_name:
            session["annotator"] = annotator_name
            return redirect(url_for("annotate"))
    return render_template("enter_name.html")


@app.route("/annotate", methods=["GET", "POST"])
def annotate():
    annotator_name = session.get("annotator")
    if not annotator_name:
        return redirect(url_for("enter_name"))

    data = load_data()
    total_rows = len(data)
    last_index = get_next_unannotated_row(annotator_name, data)

    cur_index = min(
        min(int(request.args.get("sel_index", last_index)), total_rows - 1), last_index
    )

    # If the user is submitting annotations
    if request.method == "POST":

        # Save updated data
        if "save" in request.form:
            row_id = request.form.get("row_id")
            print(request.form)
            annotation = convert_to_annotation(
                [(k, v) for k, v in request.form.items() if k.startswith("label_")]
            )

            # Update the data with the annotation
            for row in data:
                if row["doc"]["id"] == row_id:
                    row[f"annotator_{annotator_name}"] = annotation
                    break

            save_data(data)
            cur_index += 1

        if "first" in request.form:
            cur_index = 0
        if "previous" in request.form:
            cur_index = max(0, cur_index - 1)  # Move to previous
        elif "next" in request.form:
            cur_index += 1
        elif "last" in request.form:
            cur_index = last_index

        # Redirect to the updated page
        return redirect(url_for("annotate", sel_index=cur_index))

    row = data[cur_index]

    print(row["doc"])

    return render_template(
        "annotate.html",
        content=row["content"],
        row_id=row["doc"]["id"],
        annotator_name=annotator_name,
        is_annotated=f"annotator_{annotator_name}" in row,
        user_annotation=row.get(f"annotator_{annotator_name}", []),
        total_rows=total_rows,
        current_index=cur_index,
        enumerate=enumerate,
    )


@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for("enter_name"))  # Redirect to the name entry page


if __name__ == "__main__":
    app.run(debug=True)
