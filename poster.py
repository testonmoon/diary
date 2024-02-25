import os
import tkinter as tk
from html.parser import HTMLParser


NOT_REPOSITORY = """Script is not inside a git repository."""
INCORRECT_REMOTE = """Incorrect remote repository."""
UNKNOWN_MODE = """Uknown mode {}. Please report :)"""
OBLIGATORY_MISSING = """
File '{}' does not exist or is untracked.
I suggest to run git checkout manually. Also report:)
"""
OBLIGATORY_MOFIDIFED = """File '{}' is not up to sync. Please merge."""
META_REPEATED = """
Found duplicate metadata {meta} under value {old} while adding {new}.
"""
ILLEGAL_HTML_FORMAT = """
Something is wrong with the format of index.htm.
There should be only one delimiter. Please report:)
HTML:
{html}
"""


def run_command(command):
    return os.popen(command).read().strip().split('\n')


class Git:
    REMOTE = 'https://github.com/testonmoon/diary.git'
    MODIFIED = 0
    DELETED = 1
    UNTRACKED = 2

    def is_repository():
        return run_command('git status')[0].startswith('fatal')

    def is_remote_correct():
        return run_command('git config --get remote.origin.url') == Git.REMOTE

    def get_changed():
        result = {Git.MODIFIED: [], Git.DELETED: [], Git.UNTRACKED: []}
        modes = {'M': Git.MODIFIED, 'D': Git.DELETED, '??': Git.UNTRACKED}

        output = run_command('git status -s')
        for status in output:
            mode, file = status.strip().split(' ')
            if mode not in modes:
                raise Exception(UNKNOWN_MODE.format(mode))
            mode = modes[mode]
            result[mode].append(file)

        return result


class Web:
    INDEX = 'index.htm'
    DELIMITER = """<!-- GenerateHere -->"""
    LATEST = """
<div class="p-4 p-md-5 mb-4 rounded text-body-emphasis bg-body-secondary blog-newest">
  <div class="col-lg-6 px-0">
    <h1 class="display-4 fst-italic blog-title">{title}</h1>
    <p class="lead my-3 blog-content">{content}</p>
    <p class="lead my-3 blog-date">{date}</p>
    <p class="lead my-3 blog-tag">{tag}</p>
    <p class="lead mb-0"><a href="#" class="text-body-emphasis fw-bold">Read more...</a></p>
  </div>
</div>
"""
    BLOGS_CONTAINER = """
<div class="row mb-2 blog-blogs">
{posts}
</div>
"""
    POST = """
<div class="col-md-6 blog-post">
  <div class="row g-0 border rounded overflow-hidden flex-md-row mb-4 shadow-sm h-md-250 position-relative">
    <div class="col p-4 d-flex flex-column position-static">
      <strong class="d-inline-block mb-2 text-success-emphasis blog-tag">{tag}</strong>
      <h3 class="mb-0 blog-ttile">{title}</h3>
      <div class="mb-1 text-body-secondary blog-date">{date}</div>
      <p class="mb-auto blog-content">{content}</p>
      <a href="#" class="icon-link gap-1 icon-link-hover stretched-link">
        Continue reading
        <svg class="bi">
          <use xlink:href="#chevron-right" />
        </svg>
      </a>
    </div>
    <div class="col-auto d-none d-lg-block">
      <svg class="bd-placeholder-img" width="200" height="250" xmlns="http://www.w3.org/2000/svg" role="img"
        aria-label="Placeholder: No photos!" preserveAspectRatio="xMidYMid slice" focusable="false">
        <title>Placeholder</title>
        <rect width="100%" height="100%" fill="#55595c" /><text x="50%" y="50%" fill="#eceeef"
          dy=".3em">No photos!</text>
      </svg>
    </div>
  </div>
</div>
"""

    class MyHTMLParser(HTMLParser):
        CONTAINER_CLASS = 'blog-container'
        DEFAULT = 0
        COUNTING_DIVS = 1
        METADATA = ('blog-tag', 'blog-title', 'blog-date', 'blog-content')

        def __init__(self):
            super().__init__()
            self.State = self.DEFAULT
            self.Html = ''
            self.Blogs = []

        def handle_starttag(self, tag, attrs):
            if self.State != self.COUNTING_DIVS:
                self.Html += f'<{tag}'
                for k, v in attrs:
                    self.Html += f' {k}="{v}"'
                self.Html += '>'

            for k, v in attrs:
                if k != 'class':
                    break

                if v.find(self.CONTAINER_CLASS) >= 0:
                    self.State = self.COUNTING_DIVS
                    # stupid workaround
                    self.Html += f'\n{Web.DELIMITER}'
                    self.Count = 0

            if self.State == self.COUNTING_DIVS:
                self.Count += 1

            self.CurrentMeta = {}
            if self.State == self.COUNTING_DIVS:
                for k, v in attrs:
                    if k != 'class':
                        break

                    for meta in self.METADATA:
                        if v.find(meta) >= 0:
                            self.CurrentMeta[meta] = ''

        def handle_endtag(self, tag):
            if self.State == self.COUNTING_DIVS:
                self.Count -= 1
                if self.Count == 0:
                    self.State = self.DEFAULT
                    if len(self.Blogs) > 0 and len(self.Blogs[-1]) == 0:
                        self.Blogs.pop()

                if self.State != self.DEFAULT:
                    if (len(self.Blogs) == 0 or
                            len(self.Blogs[-1]) == len(self.METADATA)):
                        self.Blogs.append({})
                    current_blog = self.Blogs[-1]

                    for meta, value in self.CurrentMeta.items():
                        if meta in current_blog:
                            raise Exception(META_REPEATED.format(
                                meta, current_blog[meta], value))

                        current_blog[meta] = value

            if self.State != self.COUNTING_DIVS:
                self.Html += f'</{tag}>'

        def handle_data(self, data):
            if self.State != self.COUNTING_DIVS:
                self.Html += data
                return

            for meta in self.METADATA:
                if meta in self.CurrentMeta:
                    self.CurrentMeta[meta] += data

        def handle_comment(self, data):
            if self.State != self.COUNTING_DIVS:
                self.Html += f'<!--{data}-->'

    Parser = MyHTMLParser()
    
    def initalize():
        with open(Web.INDEX, 'r') as f:
            content = f.read()
            Web.Parser.feed(content)

    def add_blog(tag, title, date, content):
        Web.Parser.Blogs.append({'blog-tag': tag, 'blog-title': title,
                                 'blog-date': date, 'blog-content': content.replace('\n', '<br>')})

    def get_html():
        def get_generated():
            html = ''
            if len(Web.Parser.Blogs) == 0:
                return html

            if len(Web.Parser.Blogs[-1]) == 0:
                Web.Parser.Blogs.pop()

            if len(Web.Parser.Blogs) == 0:
                return html

            newest = Web.Parser.Blogs[-1]
            html += Web.LATEST.format(
                title=newest['blog-title'],
                tag=newest['blog-tag'],
                content=newest['blog-content'],
                date=newest['blog-date'])

            if len(Web.Parser.Blogs) == 1:
                return html

            posts = ''
            for blog in reversed(Web.Parser.Blogs[:-1]):
                print(Web.Parser.Blogs)
                posts += Web.POST.format(
                    title=blog['blog-title'],
                    tag=blog['blog-tag'],
                    content=blog['blog-content'],
                    date=blog['blog-date'])
            html += Web.BLOGS_CONTAINER.format(posts=posts)

            return html

        split = Web.Parser.Html.split(Web.DELIMITER)
        if len(split) != 2:
            raise Exception(ILLEGAL_HTML_FORMAT, Web.Parser.Html)

        return split[0] + get_generated() + split[1]


def check_obligatory_file(name, status):
    if not os.path.exists(name) or name in status[Git.UNTRACKED]:
        raise Exception(OBLIGATORY_MISSING.format(name))

    if name in status[Git.MODIFIED]:
        raise Exception(OBLIGATORY_MOFIDIFED.format(name))


def validate_filesystem():
    if Git.is_repository():
        raise Exception(NOT_REPOSITORY)

    if Git.is_remote_correct():
        raise Exception(INCORRECT_REMOTE)

    status = Git.get_changed()
    check_obligatory_file('index.htm', status)
    check_obligatory_file('poster.py', status)


def run_app():
    def post():
        title = name_entry.get()
        lines = content_entry.get("1.0", tk.END).splitlines()
        Web.add_blog('notag', title, 'now', '\n'.join(lines))
        generated = Web.get_html()
        with open('text.htm', 'w') as f:
            f.write(generated)

    window = tk.Tk()
    name_label = tk.Label(text="Name")
    name_label.config(font=("consolas", 12))
    name_label.grid(row=0, column=0, sticky="nsew")
    name_entry = tk.Entry()
    name_entry.grid(row=1, column=0, sticky="nsew")
    tk.Label(text="Content").grid(
        row=2, column=0, sticky="nsew")
    content_entry = tk.Text(borderwidth=3, relief="sunken")
    content_entry.config(font=("consolas", 12), undo=True, wrap='word')
    content_entry.grid(row=3, column=0, sticky="nsew")
    scrollb = tk.Scrollbar(command=content_entry.yview)
    scrollb.grid(row=3, column=1, sticky='nsew')
    content_entry['yscrollcommand'] = scrollb.set
    tk.Button(text='Post!', command=post).grid(row=4, column=0)
    window.mainloop()


def main():
    validate_filesystem()
    Web.initalize()
    run_app()


if __name__ == '__main__':
    main()

