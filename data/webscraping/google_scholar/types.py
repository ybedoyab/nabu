from typing import TypedDict, NotRequired


class Author(TypedDict):
    name: str
    link: NotRequired[str]
    author_id: NotRequired[str]
    serpapi_scholar_link: NotRequired[str]


class PublicationInfo(TypedDict):
    summary: str
    authors: list[Author]


class Resource(TypedDict):
    title: str
    file_format: str
    link: str


class CitedBy(TypedDict):
    total: int
    link: str
    cites_id: str
    serpapi_scholar_link: str


class Versions(TypedDict):
    total: int
    link: str
    cluster_id: str
    serpapi_scholar_link: str


class InlineLinks(TypedDict):
    serpapi_cite_link: str
    related_pages_link: str
    serpapi_related_pages_link: str
    html_version: NotRequired[str]
    cached_page_link: NotRequired[str]
    cited_by: NotRequired[CitedBy]
    versions: NotRequired[Versions]


class OrganicResult(TypedDict):
    position: int
    title: str
    result_id: str
    link: str
    snippet: str
    publication_info: PublicationInfo
    inline_links: InlineLinks
    type: NotRequired[str]
    resources: NotRequired[list[Resource]]
