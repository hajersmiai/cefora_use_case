from __future__ import annotations
import typer
from dotenv import load_dotenv
from db.database import engine
from db.models import Base
from scraper.writer import Writer
from scraper.stepstone import StepstoneScraper
from scraper.indeed import IndeedScraper

app = typer.Typer(help="VacaViz scraping CLI")

@app.command()
def initdb():
    """Create database tables."""
    load_dotenv()
    Base.metadata.create_all(bind=engine)
    typer.echo("DB initialized ✅")

@app.command()
def scrape(source: str = typer.Argument(..., help="stepstone|indeed"),
           query: str = typer.Option("data engineer", "--query", "-q"),
           location: str = typer.Option("Belgium", "--location", "-l"),
           pages: int = typer.Option(1, "--pages", "-p")):
    """Run scraper for a source."""
    load_dotenv()
    writer = Writer()
    if source.lower() == "stepstone":
        s = StepstoneScraper(writer)
    elif source.lower() == "indeed":
        s = IndeedScraper(writer)
    else:
        raise typer.BadParameter("Unsupported source")

    urls = s.search_urls(query=query, location=location, pages=pages)
    saved = s.run(urls)
    writer.close()
    typer.echo(f"Saved {saved} jobs from {source} ✅")

if __name__ == "__main__":
    app()
