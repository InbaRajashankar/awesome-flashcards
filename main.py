#!/usr/bin/env python3

import argparse
import csv
import random
import shutil
import sys

UNSEEN = "unseen"
SEEN = "seen"
MIN_BAR_WIDTH = 8


def load_words(csv_paths):
    words = []

    for csv_path in csv_paths:
        try:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)

                for line_number, row in enumerate(reader, start=1):
                    if len(row) < 2:
                        print(
                            f"Skipping line {line_number} in {csv_path}: "
                            "expected two columns",
                            file=sys.stderr,
                        )
                        continue

                    russian = row[0].strip()
                    english = row[1].strip()

                    if russian and english:
                        words.append((russian, english, UNSEEN))
                        words.append((english, russian, UNSEEN))

        except FileNotFoundError:
            print(f"File not found: {csv_path}", file=sys.stderr)
            sys.exit(1)
        except OSError as error:
            print(f"Could not read file {csv_path}: {error}", file=sys.stderr)
            sys.exit(1)

    random.shuffle(words)

    if not words:
        print("The CSV files contain no valid word pairs.", file=sys.stderr)
        sys.exit(1)

    return words


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def progress_bar(completed, seen, unseen):
    total = completed + seen + unseen
    columns = shutil.get_terminal_size(fallback=(80, 24)).columns
    full_label = f" {completed}/{total} completed  {seen} seen  {unseen} unseen"
    short_label = f" {completed}/{total}"
    if 2 + MIN_BAR_WIDTH + len(full_label) <= columns:
        label = full_label
    else:
        label = short_label

    bar_width = columns - 2 - len(label)
    if bar_width < 1:
        bar_width = 1

    if total <= 0:
        completed_width = seen_width = 0
        unseen_width = bar_width
    else:
        completed_width = int(bar_width * completed / total)
        seen_width = int(bar_width * seen / total)
        unseen_width = bar_width - completed_width - seen_width

    if sys.stdout.isatty():
        green, yellow, dim, reset = "\033[32m", "\033[33m", "\033[2m", "\033[0m"
        bar = (
            f"{green}{'█' * completed_width}"
            f"{yellow}{'█' * seen_width}"
            f"{dim}{'█' * unseen_width}{reset}"
        )
    else:
        bar = f"{'#' * completed_width}{'=' * seen_width}{'-' * unseen_width}"

    return f"[{bar}]{label}"


def draw_card(question, answer, total_cards, completed, seen):
    clear_screen()
    unseen = total_cards - completed - seen
    print("Flashcards")
    print(progress_bar(completed, seen, unseen))
    print("Press Enter to reveal the answer.")
    print("Press Enter again for the next card.\n")
    print(f"Question: {question}")
    if answer is not None:
        print(f"Answer: {answer}\n")
        print("1-repeat soon, 2-repeat later, 3-complete, q-quit.")


def with_state(card, state):
    question, answer, _ = card
    return (question, answer, state)


def insert_soon(word_pairs, card):
    if len(word_pairs) < 6:
        word_pairs.insert(min(1, len(word_pairs)), card)
    else:
        word_pairs.insert(random.randint(0, 5), card)


def insert_later(word_pairs, card):
    if len(word_pairs) < 16:
        word_pairs.insert(min(2, len(word_pairs)), card)
    else:
        word_pairs.insert(random.randint(5, 15), card)


def main():
    parser = argparse.ArgumentParser(
        description="Practice Russian-English vocabulary from two-column CSV files."
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        help=(
            "Paths to one or more CSV files; column 1 should be Russian "
            "and column 2 English"
        ),
    )
    args = parser.parse_args()

    word_pairs = load_words(args.csv_files)
    total_cards = len(word_pairs)
    completed = 0
    seen = 0
    finished_set = False

    while word_pairs:
        card = word_pairs.pop(0)
        question, answer, state = card

        draw_card(question, None, total_cards, completed, seen)
        input()

        draw_card(question, answer, total_cards, completed, seen)
        user_input = input("> ").strip().lower()
        if user_input == "1":
            if state == UNSEEN:
                seen += 1
            insert_soon(word_pairs, with_state(card, SEEN))
        elif user_input == "2":
            if state == UNSEEN:
                seen += 1
            insert_later(word_pairs, with_state(card, SEEN))
        elif user_input == "3":
            if state == SEEN:
                seen -= 1
            completed += 1
        elif user_input == "q":
            word_pairs.append(card)
            break
        else:
            if state == UNSEEN:
                seen += 1
            word_pairs.append(with_state(card, SEEN))
    else:
        finished_set = True

    clear_screen()
    if finished_set:
        print(progress_bar(total_cards, 0, 0))
        print("Set complete.")


if __name__ == "__main__":
    main()
