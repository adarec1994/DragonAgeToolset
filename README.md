# Dragon Age Toolset Wiki

This repository contains a GitHub-wiki-compatible export of the Dragon Age Toolset Wiki.

GitHub stores wiki pages in a separate git repository named `DragonAgeToolset.wiki.git`. This repo is set up as the source package:

1. Commit and push this repository to `main` so the image links under `assets/` are available through raw GitHub URLs.
2. Enable/create the wiki for `adarec1994/DragonAgeToolset` on GitHub with one starter page.
3. Run `.\publish-wiki.ps1` from this folder to copy the `.mediawiki` pages into `DragonAgeToolset.wiki.git`, commit them, and push the wiki.

The `.mediawiki` extension is intentional: GitHub chooses the wiki renderer from the file extension.

GitHub wiki notes:

- `Home.mediawiki` is the wiki home page.
- `_Sidebar.mediawiki` and `_Footer.mediawiki` are included for GitHub's wiki chrome.
- Images live in `assets/` in this repository instead of the wiki repo, keeping the wiki repo smaller.
- GitHub wikis have a soft limit of 5,000 total files. This exact export is larger than that, even after removing exact duplicate crawl artifacts, so GitHub Pages may be a better long-term host if GitHub wiki starts hiding pages.
- Dark mode is handled by GitHub's own theme. Custom wiki CSS is not supported in the normal GitHub wiki renderer.

Reference:

- https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages
- https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis
