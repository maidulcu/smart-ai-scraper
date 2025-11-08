"""
Command-line interface for Smart AI Scraper
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from .core.scraper import SmartScraper
from .core.config import settings
from .storage.database import DatabaseManager

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Smart AI Scraper - AI-powered web scraping tool"""
    pass


@cli.command()
@click.argument("url")
@click.option("--type", "-t", type=click.Choice(["general", "product", "article"]), default="general",
              help="Type of extraction to perform")
@click.option("--save/--no-save", default=False, help="Save results to database")
@click.option("--collection", "-c", default="scraped_data", help="Database collection name")
@click.option("--screenshot/--no-screenshot", default=False, help="Take a screenshot")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--output", "-o", type=click.Path(), help="Save output to JSON file")
def scrape(url: str, type: str, save: bool, collection: str, screenshot: bool, headless: bool, output: Optional[str]):
    """Scrape a single URL"""

    async def run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scraping {url}...", total=None)

            scraper = SmartScraper(headless=headless)
            result = await scraper.scrape(
                url=url,
                extractor_type=type,
                save_to_db=save,
                collection=collection,
                take_screenshot=screenshot,
            )

            progress.update(task, completed=True)

        if result["success"]:
            console.print(f"[green]✓ Successfully scraped {url}[/green]")

            # Display results in a table
            table = Table(title="Scraped Data")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="magenta")

            for key, value in result.items():
                if key not in ["content", "raw_data", "entities", "structured_data"]:
                    table.add_row(key, str(value)[:100])

            console.print(table)

            # Show entities if present
            if "entities" in result and result["entities"]:
                console.print("\n[bold]Extracted Entities:[/bold]")
                for entity in result["entities"][:10]:
                    console.print(f"  • {entity.get('text')} ({entity.get('label')})")

        else:
            console.print(f"[red]✗ Failed to scrape {url}[/red]")
            console.print(f"Error: {result.get('error')}")

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            console.print(f"\n[green]Saved to {output}[/green]")

        return result

    asyncio.run(run())


@cli.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--type", "-t", type=click.Choice(["general", "product", "article"]), default="general")
@click.option("--save/--no-save", default=True, help="Save results to database")
@click.option("--collection", "-c", default="scraped_data")
@click.option("--concurrent", default=3, help="Max concurrent requests")
@click.option("--output", "-o", type=click.Path(), help="Save output to JSON file")
def scrape_multiple(urls: tuple, type: str, save: bool, collection: str, concurrent: int, output: Optional[str]):
    """Scrape multiple URLs"""

    async def run():
        console.print(f"Scraping {len(urls)} URLs with {concurrent} concurrent requests...")

        scraper = SmartScraper()
        results = await scraper.scrape_multiple(
            urls=list(urls),
            extractor_type=type,
            save_to_db=save,
            collection=collection,
            max_concurrent=concurrent,
        )

        # Summary
        successful = sum(1 for r in results if r.get("success"))
        console.print(f"\n[green]Completed: {successful}/{len(urls)} successful[/green]")

        # Display results table
        table = Table(title="Scraping Results")
        table.add_column("URL", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Title", style="green")

        for result in results:
            status = "✓" if result.get("success") else "✗"
            title = result.get("title", result.get("name", "N/A"))[:50]
            table.add_row(result["url"][:60], status, title)

        console.print(table)

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"\n[green]Saved to {output}[/green]")

        return results

    asyncio.run(run())


@cli.command()
@click.argument("start_url")
@click.option("--depth", default=2, help="Maximum crawl depth")
@click.option("--max-pages", default=50, help="Maximum pages to crawl")
@click.option("--same-domain/--all-domains", default=True, help="Restrict to same domain")
@click.option("--type", "-t", type=click.Choice(["general", "product", "article"]), default="general")
@click.option("--save/--no-save", default=True, help="Save results to database")
@click.option("--collection", "-c", default="scraped_data")
def crawl(start_url: str, depth: int, max_pages: int, same_domain: bool, type: str, save: bool, collection: str):
    """Crawl a website starting from a URL"""

    async def run():
        console.print(f"Starting crawl from {start_url}")
        console.print(f"Max depth: {depth}, Max pages: {max_pages}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Crawling...", total=None)

            scraper = SmartScraper()
            results = await scraper.crawl(
                start_url=start_url,
                max_depth=depth,
                max_pages=max_pages,
                same_domain_only=same_domain,
                extractor_type=type,
                save_to_db=save,
                collection=collection,
            )

            progress.update(task, completed=True)

        console.print(f"\n[green]Crawl completed: {len(results)} pages scraped[/green]")

        return results

    asyncio.run(run())


@cli.command()
@click.argument("collection")
@click.option("--limit", default=10, help="Number of records to show")
def query(collection: str, limit: int):
    """Query scraped data from database"""
    try:
        db = DatabaseManager()
        results = db.find(collection, {})[:limit]

        if not results:
            console.print(f"[yellow]No data found in collection '{collection}'[/yellow]")
            return

        # Display results
        table = Table(title=f"Data from '{collection}'")
        table.add_column("ID", style="cyan")
        table.add_column("URL", style="blue")
        table.add_column("Title", style="green")
        table.add_column("Created", style="magenta")

        for result in results:
            row_id = result.get("_id", result.get("id", "N/A"))
            url = result.get("url", "N/A")[:50]
            title = result.get("title", result.get("name", "N/A"))[:40]
            created = str(result.get("created_at", "N/A"))[:19]
            table.add_row(str(row_id), url, title, created)

        console.print(table)
        console.print(f"\nShowing {len(results)} of total records")

        db.close()

    except Exception as e:
        console.print(f"[red]Error querying database: {e}[/red]")


@cli.command()
def worker():
    """Start Celery worker for distributed scraping"""
    import subprocess

    console.print("[yellow]Starting Celery worker...[/yellow]")
    console.print("Press Ctrl+C to stop\n")

    try:
        subprocess.run([
            "celery",
            "-A", "smart_ai_scraper.tasks.celery_app",
            "worker",
            "--loglevel=info"
        ])
    except KeyboardInterrupt:
        console.print("\n[yellow]Worker stopped[/yellow]")


@cli.command()
def config():
    """Show current configuration"""
    table = Table(title="Smart AI Scraper Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    # App settings
    table.add_row("App Name", settings.app.app_name)
    table.add_row("Debug", str(settings.app.debug))
    table.add_row("Log Level", settings.app.log_level)

    # Browser settings
    table.add_row("Browser Type", settings.browser.browser_type)
    table.add_row("Headless", str(settings.browser.headless))

    # Database settings
    table.add_row("Database Type", settings.database.database_type)

    # Rate limiting
    table.add_row("Rate Limit Enabled", str(settings.rate_limit.rate_limit_enabled))
    table.add_row("Requests/Minute", str(settings.rate_limit.requests_per_minute))

    # Ethical scraping
    table.add_row("Respect robots.txt", str(settings.ethical.respect_robots_txt))
    table.add_row("Crawl Delay", f"{settings.ethical.crawl_delay}s")

    console.print(table)


@cli.command()
def setup():
    """Setup assistant for first-time configuration"""
    console.print("[bold]Smart AI Scraper Setup[/bold]\n")

    # Create .env file if it doesn't exist
    env_path = Path(".env")

    if env_path.exists():
        console.print("[yellow].env file already exists[/yellow]")
        if not click.confirm("Overwrite?"):
            return

    # Ask for settings
    console.print("\n[bold]Database Configuration[/bold]")
    db_type = click.prompt(
        "Database type",
        type=click.Choice(["mongodb", "postgres"]),
        default="mongodb"
    )

    if db_type == "mongodb":
        mongodb_uri = click.prompt("MongoDB URI", default="mongodb://localhost:27017/")
        mongodb_db = click.prompt("MongoDB Database", default="smart_scraper")

        env_content = f"""DATABASE_TYPE=mongodb
MONGODB_URI={mongodb_uri}
MONGODB_DB_NAME={mongodb_db}
"""
    else:
        pg_host = click.prompt("PostgreSQL Host", default="localhost")
        pg_user = click.prompt("PostgreSQL User", default="postgres")
        pg_pass = click.prompt("PostgreSQL Password", hide_input=True)
        pg_db = click.prompt("PostgreSQL Database", default="smart_scraper")

        env_content = f"""DATABASE_TYPE=postgres
POSTGRES_HOST={pg_host}
POSTGRES_USER={pg_user}
POSTGRES_PASSWORD={pg_pass}
POSTGRES_DB={pg_db}
"""

    # Write .env file
    with open(".env", "w") as f:
        f.write(env_content)

    console.print("\n[green]✓ Configuration saved to .env[/green]")

    # Download spaCy model
    console.print("\n[bold]Downloading spaCy model...[/bold]")
    if click.confirm("Download en_core_web_sm model?", default=True):
        import subprocess
        try:
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            console.print("[green]✓ spaCy model downloaded[/green]")
        except Exception as e:
            console.print(f"[red]Error downloading spaCy model: {e}[/red]")

    # Install Playwright browsers
    console.print("\n[bold]Installing Playwright browsers...[/bold]")
    if click.confirm("Install Playwright browsers?", default=True):
        import subprocess
        try:
            subprocess.run(["playwright", "install", "chromium"])
            console.print("[green]✓ Playwright browsers installed[/green]")
        except Exception as e:
            console.print(f"[red]Error installing Playwright: {e}[/red]")

    console.print("\n[green]✓ Setup complete![/green]")
    console.print("\nYou can now run: smart-scraper scrape <url>")


def main():
    """Main entry point"""
    # Configure logger
    logger.remove()
    logger.add(
        Path(settings.storage.logs_dir) / "scraper.log",
        rotation="1 day",
        retention="7 days",
        level=settings.app.log_level,
    )

    cli()


if __name__ == "__main__":
    main()
