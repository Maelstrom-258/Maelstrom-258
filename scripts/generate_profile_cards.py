#!/usr/bin/env python3
"""Generate self-hosted SVG cards for the GitHub profile README."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
API = "https://api.github.com"
PROFILE_REPO = USERNAME.lower()
COLORS = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "Java": "#b07219",
    "Shell": "#89e051",
    "C#": "#178600",
    "C++": "#f34b7d",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Vue": "#41b883",
}


def github_get(path: str):
    request = Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{USERNAME}-profile-readme",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code} for {path}") from None


def list_public_repositories():
    repositories = []
    page = 1
    while True:
        batch = github_get(
            f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100&page={page}"
        )
        if not batch:
            break
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repositories


def svg_start(title: str, width: int, height: int, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">',
        '<rect width="100%" height="100%" rx="14" fill="#0d1117" stroke="#30363d"/>',
        f'<text x="24" y="34" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="17" font-weight="700">{html.escape(title)}</text>',
        f'<text x="24" y="55" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">{html.escape(subtitle)}</text>',
    ]


def write_stats(user, repositories):
    stars = sum(repo["stargazers_count"] for repo in repositories if not repo["fork"])
    forks = sum(repo["forks_count"] for repo in repositories if not repo["fork"])
    metrics = [
        ("Repositórios públicos", str(len(repositories))),
        ("Seguidores", str(user["followers"])),
        ("Stars recebidas", str(stars)),
        ("Forks recebidos", str(forks)),
    ]
    svg = svg_start("Resumo do GitHub", 495, 180, "Dados dos repositórios públicos")
    positions = [(24, 100), (260, 100), (24, 150), (260, 150)]
    for (label, value), (x, y) in zip(metrics, positions):
        svg.append(
            f'<text x="{x}" y="{y}" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">{html.escape(label)}</text>'
        )
        svg.append(
            f'<text x="{x}" y="{y + 24}" fill="#58a6ff" font-family="Segoe UI, Arial, sans-serif" font-size="19" font-weight="700">{html.escape(value)}</text>'
        )
    svg.append("</svg>")
    Path("profile/stats.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


def write_languages(repositories):
    totals = {}
    for repo in repositories:
        if repo["fork"] or repo["name"].lower() == PROFILE_REPO:
            continue
        languages = github_get(f"/repos/{repo['full_name']}/languages")
        for language, byte_count in languages.items():
            totals[language] = totals.get(language, 0) + byte_count

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:6]
    total_bytes = sum(totals.values())
    svg = svg_start("Linguagens mais usadas", 495, 210, "Distribuição por tamanho de código nos repositórios públicos")
    if not ranked or not total_bytes:
        svg.append('<text x="24" y="112" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="13">Ainda não há dados de código para exibir.</text>')
    else:
        bar_x, bar_y, bar_width = 24, 76, 447
        cursor = bar_x
        for language, byte_count in ranked:
            segment_width = bar_width * byte_count / total_bytes
            svg.append(
                f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment_width:.2f}" height="9" fill="{COLORS.get(language, "#8b949e")}"/>'
            )
            cursor += segment_width
        for index, (language, byte_count) in enumerate(ranked):
            column = index % 2
            row = index // 2
            x = 24 + column * 236
            y = 112 + row * 30
            percentage = byte_count * 100 / total_bytes
            svg.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="4" fill="{COLORS.get(language, "#8b949e")}"/>')
            svg.append(
                f'<text x="{x + 16}" y="{y}" fill="#c9d1d9" font-family="Segoe UI, Arial, sans-serif" font-size="12">{html.escape(language)}</text>'
            )
            svg.append(
                f'<text x="{x + 214}" y="{y}" text-anchor="end" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">{percentage:.1f}%</text>'
            )
    svg.append("</svg>")
    Path("profile/languages.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


def main():
    Path("profile").mkdir(exist_ok=True)
    user = github_get(f"/users/{USERNAME}")
    repositories = list_public_repositories()
    write_stats(user, repositories)
    write_languages(repositories)


if __name__ == "__main__":
    main()
