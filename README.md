# Drasil - Static Site Generator Usage & Architecture Guide

**Drasil** is a simple, flexible, and extensible Python static site generator built around a hook-based plugin system.

---

## 1. Command Line Interface (CLI) — `drasil.py`

The `drasil.py` file serves as the main entry point of the program, handling command-line argument parsing and initializing the build process.

### Syntax
```bash
drasil -o <output_dir> [--src <src_dir>] [-y] [-v|-vv|-vvv]
```

### Command Line Options
* `-o`, `--out`: **(Required for build)** Destination directory where the compiled site will be generated.
* `--src`: Root directory of the site source code (Default: `.`).
* `-y`: Force affirmative ("YES") answer to all prompts (e.g., overwriting or cleaning the output folder).
* `-l`, `--plugin-list`: Lists all installed/detected plugins and exits.
* `--plugin-help <plugin_name>`: Displays detailed help and parameters for a specific plugin.
* `-v`, `-vv`, `-vvv`: Increases log verbosity level (`WARNING`, `INFO`, `DEBUG`).
* `--version`: Prints Drasil version and exits.

### Usage Examples
```bash
# Basic compilation of the current source site into the 'dist' folder
drasil --src ./my_website -o ./dist -y

# Display installed plugins
drasil --plugin-list

# Specific help for the Thumbnailer plugin
drasil --plugin-help Thumbnailer
```

---

## 2. Rendering Engine & Traversal — `drasil_bifrost.py`

The `DrasilBifrost` module is the core of the static generator. It handles recursively scanning the source directory tree and compiling HTML pages, directory indexes, and assets.

### File and Directory Naming Conventions
Drasil uses special prefixes and characters to control rendering and navigation menus:

| Marker | Example | Description |
| :--- | :--- | :--- |
| `_` | `_template.html`, `_draft/` | Files or folders ignored during traversal and in navigation menus. |
| `.` | `.git`, `.DS_Store` | Hidden files or folders (ignored). |
| `$` | `$secret.html` | The file is generated, but does **not** appear in navigation menus (`NO_LINK_MARKER`). |
| `%` | `%blog/` | Orders folder contents by file modification date instead of alphabetically. |
| `NN_` | `01_home.html` | Numeric prefix (e.g., `01_`, `02_`) to force ordering in menus. The prefix is removed from the displayed name and final URL. |

### Built-in Placeholders and Hooks in Templates
In HTML templates or source files, the following built-in placeholders can be used:

* `[%VER%]`: Replaced with the current version of Drasil.
* `[%PAGE_TITLE%]`: Page title extracted from the current file/folder name.
* `[%BODY%]`: Insertion point for the page content.
* `[%LAST_UPDATE%]`: Date and time of the last modification of the source file.
* `[%NAV_MENU%]`: Automatically generates HTML navigation menus for ancestors, siblings, and children.
* `[%TREE_GEN%]`: Generates a graphical HTML tree of the site directory structure.

---

## 3. Plugin Architecture & Context — `drasil_plugins.py` & `drasil_context.py`

### Plugin Management System (`DrasilPlugin`)
Plugins are automatically loaded from the `drasil/src/plugins` folder. Every plugin inherits from and implements the `DrasilPlug` class by defining:
* **Lifecycle Phases**:
  * `pre(*args)`: Executed before traversing the file tree.
  * `run(*args)`: Executed whenever a matching hook is found in text (syntax `[$hook_name:arg1:arg2$]`).
  * `post(*args)`: Executed after generating the entire site (e.g., to save summary pages).

### Rendering Context (`DrasilContext`)
During hook execution, a `DrasilContext` object containing information about the current rendering state is passed to the plugin:
* `src_root`: Source root directory.
* `output_dir`: Build target directory.
* `current_node`: Path of the file or folder currently being processed.
* `current_level`: Depth level in the directory tree.
* `siblings` / `children` / `ancestor_siblings`: Data structures related to navigation.

---

## 4. Included Plugins Reference

Plugins are invoked in source files or templates using the syntax: `[$hook_name:argument1:argument2$]`.

### 1. GIT_tag (`gittag.py`)
* **Hook:** `gittag`
* **Description:** Prints the current Git tag of the repository.
* **Syntax:** `[$gittag$]`

### 2. DDate (`ddate.py`)
* **Hook:** `DDATE`
* **Description:** Prints the current date according to the Discordian calendar.
* **Syntax:** `[$DDATE$]`

### 3. GIT_log (`gitlog.py`)
* **Hook:** `gitlog`
* **Description:** Generates a summary HTML log of Git commits from the source repository.
* **Syntax:** `[$gitlog$]`

### 4. Tag (`tag.py`)
* **Hook:** `tag`
* **Description:** Categorizes the page with tags and automatically generates summary pages (`tag_<tag_name>.html`) in the `post-build` phase.
* **Syntax:** `[$tag:programming:python:web$]`

### 5. Thumbnailer (`thumbnailer.py`)
* **Hook:** `thumbnailer`
* **Description:** Resizes an image to the specified width, creates a thumbnail, and generates the HTML tag with a link to the high-resolution image.
* **Syntax:** `[$thumbnailer:assets/photo.jpg:300:Photo description$]`

### 6. Today (`today.py`)
* **Hook:** `today`
* **Description:** Returns today's date in ISO-8601 format (`YYYY-MM-DD`).
* **Syntax:** `[$today$]`

# Drasil Plugins Usage Guide

Complete documentation of available plugins for generating sites with Drasil.

---

## 1. GIT_tag (`gittag.py`)

* **Name:** `GIT_tag`
* **Hook:** `gittag`
* **Description:** Prints the current Git tag of the source site repository.

### Syntax / Usage
```text
[$gittag$]
```

### Details
Requires no arguments. Executes `git describe --tags` on the root source directory. If the repository is not a Git repo or an error occurs, it returns:
`[gittag: ERROR, NOT A GIT REPO]`

---

## 2. DDate (`ddate.py`)

* **Name:** `DDate`
* **Hook:** `DDATE`
* **Description:** Prints the current date according to the Discordian calendar.

### Syntax / Usage
```text
[$DDATE$]
```

### Details
Requires no arguments. Uses the `ddate` library to format today's date in Discordian format (removing the "Today is" string).

---

## 3. GIT_log (`gitlog.py`)

* **Name:** `GIT_log`
* **Hook:** `gitlog`
* **Description:** Prints a summary log of Git commits from the source repository.

### Syntax / Usage
```text
[$gitlog$]
```

### Details
Requires no arguments. Retrieves commit history by running `git log --pretty=oneline` and exports formatted HTML elements:
```html
<div class="git_log_entry">
    <span class="git_hash">...</span>
    <span class="git_commit_msg">...</span>
</div>
```
If the source site is not a Git repository, it returns:
`[gitlog: ERROR, NOT A GIT REPO]`

---

## 4. Tag (`tag.py`)

* **Name:** `Tag`
* **Hook:** `tag`
* **Description:** Handles page categorization via tags and automatically generates summary pages for each tag.

### Syntax / Usage
```text
[$tag:tag_one:tag_two:tag_three$]
```

### Details
* **Arguments:** One or more tags separated by colons `:`
* **In-page Markup:** Inserts an HTML block at the trigger point containing links to the specified tags:
  ```html
  <div class="tag_list">
      <span class="tag_link"><a href="tag_tag_one.html">TAG_ONE</a></span>
      ...
  </div>
  ```
* **Post-build Generation:** In the post-build phase, automatically creates a `tag_<tag_name>.html` page for each registered tag, listing all pages that contain it.

---

## 5. Thumbnailer (`thumbnailer.py`)

* **Name:** `Thumbnailer`
* **Hook:** `thumbnailer`
* **Description:** Resizes an image to generate a thumbnail and returns the HTML tag to display it with a link to the original image.

### Syntax / Usage
```text
[$thumbnailer:path/image.jpg:width_px:Image caption$]
```

### Parameters
1. `path/image.jpg`: Relative path of the source image.
2. `width_px`: Thumbnail width in pixels (height is calculated proportionally).
3. `Caption`: Image text or caption.

### Details
Generates the thumbnail in the destination directory, saving it with the prefix `thumb_` (e.g., `thumb_image.jpg`), and returns the HTML code:
```html
<div class="picture">
    <a href="path/image.jpg" alt="image.jpg">
        <img src="path/thumb_image.jpg">
        Image caption 
        <span class="picture_specs">1920x1080 245.0 kB</span>
    </a>
</div>
```

---

## 6. Today (`today.py`)

* **Name:** `Today`
* **Hook:** `today`
* **Description:** Prints the current date in ISO-8601 format (`YYYY-MM-DD`).

### Syntax / Usage
```text
[$today$]
```

### Details
Requires no arguments. Returns today's date formatted as `YYYY-MM-DD` (e.g., `2023-10-25`).