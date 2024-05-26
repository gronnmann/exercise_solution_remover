import argparse
import os
import shutil

import cv2
import img2pdf
import numpy as np
from pdf2image import convert_from_path


def pdf_to_imgs(pdf_filename, output_folder):
    pages = convert_from_path(pdf_filename, dpi=300)
    for i, page in enumerate(pages):
        page.save(f"{output_folder}/page_{i}.png", 'PNG')


def remove_solution(img_folder):
    for img_name in os.listdir(img_folder):
        if not img_name.endswith(".png"):
            continue
        if not img_name.startswith("page"):
            continue

        img = cv2.imread(f"{img_folder}/{img_name}")

        # Red HSV mask

        # https://cvexplained.wordpress.com/2020/04/28/color-detection-hsv/
        # lower boundary RED color range values; Hue (0 - 10)
        lower1 = np.array([0, 100, 20])
        upper1 = np.array([10, 255, 255])

        # upper boundary RED color range values; Hue (160 - 180)
        lower2 = np.array([160, 100, 20])
        upper2 = np.array([179, 255, 255])

        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        lower_mask = cv2.inRange(img, lower1, upper1)
        upper_mask = cv2.inRange(img, lower2, upper2)

        mask = cv2.bitwise_or(lower_mask, upper_mask)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        img[mask > 0] = [255, 255, 255]
        cv2.imwrite(f"{img_folder}/cv_{img_name}", img)

        print(f"Removed solution from {img_name}")


def reconstruct_pdf(img_folder, file_name):

    imgs = []

    for img_name in os.listdir(img_folder):
        if not img_name.endswith(".png"):
            continue
        if not img_name.startswith("cv_"):
            continue

        imgs.append(f"{img_folder}/{img_name}")

    # Sort by page number
    imgs.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

    with open(f"{file_name}", "wb") as f:
        f.write(img2pdf.convert(imgs))

if __name__ == "__main__":
    args = argparse.ArgumentParser()

    args.add_argument("-i", type=str, required=True, help="Input PDF file")

    file_name = args.parse_args().i
    file_name_output = file_name.split(".")[0] + "_no_solutions.pdf"

    if not os.path.exists(file_name):
        print("File not found")
        exit(1)

    print(f"Removing solutions from {file_name}")

    if not os.path.exists("temp"):
        os.mkdir("temp")

    print("Converting PDF to images")
    pdf_to_imgs(file_name, "temp")

    print("Removing solutions")
    remove_solution("temp")

    print(f"Reconstructing PDF. Saving as {file_name_output}")
    reconstruct_pdf("temp", file_name_output)
    # remove temp folder
    shutil.rmtree("temp")
