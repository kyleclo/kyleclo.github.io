import os
import sys

# GitHub file size limit (100 MB)
GITHUB_FILE_SIZE_LIMIT = 100 * 1024 * 1024  # 100 MB in bytes


def check_file_sizes(directory):
    large_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)

            if file_size > GITHUB_FILE_SIZE_LIMIT:
                large_files.append((file_path, file_size))

    return large_files


def main():
    assets_dir = "assets/"

    if not os.path.exists(assets_dir):
        print(f"Error: The directory '{assets_dir}' does not exist.")
        sys.exit(1)

    large_files = check_file_sizes(assets_dir)

    if large_files:
        print("The following files exceed GitHub's file size limit (100 MB):")
        for file_path, file_size in large_files:
            print(f"{file_path}: {file_size / 1024 / 1024:.2f} MB")
    else:
        print(
            "All files in the 'assets/' directory and its subdirectories are within GitHub's file size limit."
        )


if __name__ == "__main__":
    main()
