from ebooklib import epub
import tempfile


class EPUBExporter:
    def export_project(self, project, chapters):
        book = epub.EpubBook()

        book.set_identifier(f"project-{project.id}")
        book.set_title(project.title)
        book.set_language("en")
        book.add_author(project.author_name or "Unknown Author")

        epub_chapters = []

        for idx, chapter in enumerate(chapters, start=1):
            c = epub.EpubHtml(
                title=chapter.title,
                file_name=f"chap_{idx}.xhtml",
                lang="en"
            )
            content = chapter.content or ""
            c.content = f"<h1>{chapter.title}</h1><p>{content}</p>"
            book.add_item(c)
            epub_chapters.append(c)

        book.toc = tuple(epub_chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        book.spine = ["nav"] + epub_chapters

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".epub")
        epub.write_epub(tmp_file.name, book)

        return tmp_file.name
