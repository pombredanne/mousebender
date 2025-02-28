"""Tests for mousebender.simple."""
import warnings

import importlib_resources
import packaging.specifiers
import packaging.version
import pytest

from mousebender import simple

from .data import simple as simple_data


class TestProjectURLConstruction:

    """Tests for mousebender.simple.create_project_url()."""

    @pytest.mark.parametrize("base_url", ["/simple/", "/simple"])
    def test_url_joining(self, base_url):
        url = simple.create_project_url(base_url, "hello")
        assert url == "/simple/hello/"

    def test_project_name_lowercased(self):
        url = simple.create_project_url("/", "THEPROJECTNAME")
        assert url == "/theprojectname/"

    def test_project_name_normalized(self):
        normal_url = simple.create_project_url("/", "the_project.name.-_.-_here")
        assert normal_url == "/the-project-name-here/"

    def test_only_project_name_in_url_normalized(self):
        url = simple.create_project_url(
            "https://terribly_awesome.com/So/Simple/", "THE_project.name.-_.-_here"
        )
        assert url == "https://terribly_awesome.com/So/Simple/the-project-name-here/"

    def test_no_base_url(self):
        url = simple.create_project_url("", "django-node")
        assert url == "django-node/"


class TestRepoIndexParsing:

    """Tests for mousebender.simple.parse_repo_index()."""

    @pytest.mark.parametrize(
        "name,count,expected_item",
        [
            ("pypi", 212_862, ("numpy", "/simple/numpy/")),
            ("piwheels", 263_872, ("django-node", "django-node/")),
        ],
    )
    def test_full_parse(self, name, count, expected_item):
        index_file = importlib_resources.files(simple_data) / f"index.{name}.html"
        index_html = index_file.read_text(encoding="utf-8")
        index = simple.parse_repo_index(index_html)
        assert len(index) == count
        key, value = expected_item
        assert key in index
        assert index[key] == value

    def test_no_cdata(self):
        index_html = (
            "<html><head></head><body><a href='https://no.url/here'></a></body></html>"
        )
        index = simple.parse_repo_index(index_html)
        assert not index

    def test_no_href(self):
        index_html = "<html><head></head><body><a>my-cdata-package</a></body></html>"
        index = simple.parse_repo_index(index_html)
        assert not index

    def test_project_url_normalization_complete(self):
        index_html = """
            <html>
                <body>
                    <a href="/project/PACKAGE-NAME">package-name</a>
                </body>
            </html>
        """
        index = simple.parse_repo_index(index_html)
        assert index["package-name"] == "/project/package-name/"

    def test_project_name_not_normalized(self):
        index_html = """
            <html>
                <body>
                    <a href="/project/package-name">PACKAGE-NAME</a>
                </body>
            </html>
        """
        index = simple.parse_repo_index(index_html)
        assert index["PACKAGE-NAME"] == "/project/package-name/"

    def test_relative_url(self):
        index_html = """
            <html>
                <body>
                    <a href="django-node">django-node</a>
                </body>
            </html>
        """
        index = simple.parse_repo_index(index_html)
        assert index["django-node"] == "django-node/"


class TestArchiveLink:

    """Tests for mousebender.simple.ArchiveLink."""

    @pytest.mark.parametrize(
        "archive_link",
        [
            simple.ArchiveLink(filename="B", url="A/B"),
            simple.ArchiveLink(
                filename="B",
                url="A/B",
                requires_python=packaging.specifiers.SpecifierSet(">=3.6"),
            ),
            simple.ArchiveLink(
                filename="B",
                url="A/B",
                hash_=("sha256", "ABCDEF"),
            ),
            simple.ArchiveLink(
                filename="B",
                url="A/B",
                gpg_sig=True,
            ),
            simple.ArchiveLink(filename="B", url="A/B", yanked=""),
            simple.ArchiveLink(filename="B", url="A/B", yanked="oops!"),
            simple.ArchiveLink(filename="B", url="A/B", metadata=("", "")),
            simple.ArchiveLink(filename="B", url="A/B", metadata=("sha256", "ABCDEF")),
            simple.ArchiveLink(
                filename="B",
                url="A/B",
                requires_python=packaging.specifiers.SpecifierSet(">=3.6"),
                hash_=("sha256", "ABCDEF"),
                gpg_sig=True,
                yanked="oops!",
                metadata=("sha512", "GHIJKL"),
            ),
        ],
    )
    def test_str(self, archive_link):
        """Make sure __str__ roundtrips."""
        html = str(archive_link)
        roundtrip = simple.parse_archive_links(html)
        assert len(roundtrip) == 1
        print(html)
        print(roundtrip[0])
        assert archive_link == roundtrip[0]

    def test_str_escaping(self):
        """data-requires-python must have an escaped value."""
        archive_link = simple.ArchiveLink(
            filename="B",
            url="A/B",
            requires_python=packaging.specifiers.SpecifierSet(">=3.6"),
        )
        assert "gt;=3.6" in str(archive_link)


class TestParseArchiveLinks:

    """Tests for mousebender.simple.parse_archive_links()."""

    @pytest.mark.parametrize(
        "module_name,count,expected_archive_link",
        [
            (
                "numpy",
                1402,
                simple.ArchiveLink(
                    filename="numpy-1.13.0rc1-cp36-none-win_amd64.whl",
                    url="https://files.pythonhosted.org/packages/5c/2e/5c0eee0635035a7e0646734e2b9388e17a97f6f2087e15141a218b6f2b6d/numpy-1.13.0rc1-cp36-none-win_amd64.whl",
                    requires_python=packaging.specifiers.SpecifierSet(
                        ">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*"
                    ),
                    hash_=(
                        "sha256",
                        "8e8e1ccf025c8b6a821f75086a364a68d9e1877519a35bf8facec9e5120836f4",
                    ),
                    gpg_sig=None,
                    yanked=None,
                    metadata=None,
                ),
            ),
            (
                "pulpcore-client",
                370,
                simple.ArchiveLink(
                    filename="pulpcore_client-3.1.0.dev1578940535-py3-none-any.whl",
                    url="https://files.pythonhosted.org/packages/ca/7e/e14e41dc4bc60208f597f346d57755636e882be7509179c4e7c11f2c60a9/pulpcore_client-3.1.0.dev1578940535-py3-none-any.whl",
                    requires_python=packaging.specifiers.SpecifierSet(),
                    hash_=(
                        "sha256",
                        "83a3759d7b6af33083b0d4893d53615fc045cbad9adde68a8df02e25b1862bc6",
                    ),
                    gpg_sig=None,
                    yanked=None,
                    metadata=None,
                ),
            ),
            (
                "pytorch",
                522,
                simple.ArchiveLink(
                    filename="torchvision-0.5.0+cu100-cp36-cp36m-linux_x86_64.whl",
                    url="cu100/torchvision-0.5.0%2Bcu100-cp36-cp36m-linux_x86_64.whl",
                    requires_python=packaging.specifiers.SpecifierSet(),
                    hash_=None,
                    gpg_sig=None,
                    yanked=None,
                    metadata=None,
                ),
            ),
            (
                "AICoE-tensorflow",
                15,
                simple.ArchiveLink(
                    filename="tensorflow-2.0.0-cp37-cp37m-linux_x86_64.whl",
                    url="tensorflow-2.0.0-cp37-cp37m-linux_x86_64.whl",
                    requires_python=packaging.specifiers.SpecifierSet(),
                    hash_=None,
                    gpg_sig=None,
                    yanked=None,
                    metadata=None,
                ),
            ),
            (
                "numpy-piwheels",
                316,
                simple.ArchiveLink(
                    filename="numpy-1.10.4-cp35-cp35m-linux_armv7l.whl",
                    url="numpy-1.10.4-cp35-cp35m-linux_armv7l.whl",
                    requires_python=packaging.specifiers.SpecifierSet(),
                    hash_=(
                        "sha256",
                        "5768279588a4766adb0211bbaa0f5857be38483c5aafe5d1caecbcd32749966e",
                    ),
                    gpg_sig=None,
                    yanked=None,
                    metadata=None,
                ),
            ),
        ],
    )
    def test_full_parse(self, module_name, count, expected_archive_link):
        html_file = (
            importlib_resources.files(simple_data) / f"archive_links.{module_name}.html"
        )
        html = html_file.read_text(encoding="utf-8")
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == count
        assert expected_archive_link in archive_links

    @pytest.mark.parametrize(
        "html,expected_filename",
        [
            (
                '<a href="https://files.pythonhosted.org/packages/92/e2/7d9c6894511337b012735c0c149a7b4e49db0b934798b3ae05a3b46f31f0/numpy-1.12.1-cp35-none-win_amd64.whl#sha256=818d5a1d5752d09929ce1ba1735366d5acc769a1839386dc91f3ac30cf9faf19">numpy-1.12.1-cp35-none-win_amd64.whl</a><br/>',
                "numpy-1.12.1-cp35-none-win_amd64.whl",
            ),
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                "torch-1.2.0+cpu-cp35-cp35m-win_amd64.whl",
            ),
        ],
    )
    def test_filename(self, html, expected_filename):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert archive_links[0].filename == expected_filename

    @pytest.mark.parametrize(
        "html,expected_url",
        [
            (
                '<a href="https://files.pythonhosted.org/packages/92/e2/7d9c6894511337b012735c0c149a7b4e49db0b934798b3ae05a3b46f31f0/numpy-1.12.1-cp35-none-win_amd64.whl#sha256=818d5a1d5752d09929ce1ba1735366d5acc769a1839386dc91f3ac30cf9faf19">numpy-1.12.1-cp35-none-win_amd64.whl</a><br/>',
                "https://files.pythonhosted.org/packages/92/e2/7d9c6894511337b012735c0c149a7b4e49db0b934798b3ae05a3b46f31f0/numpy-1.12.1-cp35-none-win_amd64.whl",
            ),
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                "cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl",
            ),
        ],
    )
    def test_url(self, html, expected_url):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert archive_links[0].url == expected_url

    @pytest.mark.parametrize(
        "html,supported,unsupported",
        [
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                "3.8",
                None,
            ),
            (
                '<a href="https://files.pythonhosted.org/packages/4e/d9/d7ec4b9508e6a89f80de3e18fe3629c3c089355bec453b55e271c53dd23f/numpy-1.13.0-cp34-none-win32.whl#sha256=560ca5248c2a8fd96ac75a05811eca0ce08dfeea2ee128c87c9c7261af366288" data-requires-python="&gt;=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*">numpy-1.13.0-cp34-none-win32.whl</a><br/>',
                "2.7",
                "3.3",
            ),
        ],
    )
    def test_requires_python(self, html, supported, unsupported):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert packaging.version.Version(supported) in archive_links[0].requires_python
        if unsupported:
            assert (
                packaging.version.Version(unsupported)
                not in archive_links[0].requires_python
            )

    @pytest.mark.parametrize(
        "html,expected_hash",
        [
            (
                '<a href="https://files.pythonhosted.org/packages/92/e2/7d9c6894511337b012735c0c149a7b4e49db0b934798b3ae05a3b46f31f0/numpy-1.12.1-cp35-none-win_amd64.whl#sha256=818d5a1d5752d09929ce1ba1735366d5acc769a1839386dc91f3ac30cf9faf19">numpy-1.12.1-cp35-none-win_amd64.whl</a><br/>',
                (
                    "sha256",
                    "818d5a1d5752d09929ce1ba1735366d5acc769a1839386dc91f3ac30cf9faf19",
                ),
            ),
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                None,
            ),
        ],
    )
    def test_hash_(self, html, expected_hash):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert archive_links[0].hash_ == expected_hash

    @pytest.mark.parametrize(
        "html,expected_gpg_sig",
        [
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                None,
            ),
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl" data-gpg-sig="true">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                True,
            ),
            (
                '<a href="cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl" data-gpg-sig="false">cpu/torch-1.2.0%2Bcpu-cp35-cp35m-win_amd64.whl</a><br>',
                False,
            ),
        ],
    )
    def test_gpg_sig(self, html, expected_gpg_sig):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert archive_links[0].gpg_sig == expected_gpg_sig

    @pytest.mark.parametrize(
        "html,expected",
        [
            (
                '<a href="spam-1.2.3-py3.none.any.whl" data-yanked>spam-1.2.3-py3.none.any.whl</a>',
                "",
            ),
            (
                '<a href="spam-1.2.3-py3.none.any.whl" data-yanked="oops!">spam-1.2.3-py3.none.any.whl</a>',
                "oops!",
            ),
            (
                '<a href="spam-1.2.3-py3.none.any.whl" data-yanked="">spam-1.2.3-py3.none.any.whl</a>',
                "",
            ),
            (
                '<a href="spam-1.2.3-py3.none.any.whl">spam-1.2.3-py3.none.any.whl</a>',
                None,
            ),
        ],
    )
    def test_yanked(self, html, expected):
        archive_links = simple.parse_archive_links(html)
        assert len(archive_links) == 1
        assert archive_links[0].yanked == expected


@pytest.mark.parametrize(
    "parser", [simple.parse_repo_index, simple.parse_archive_links]
)
class TestPEP629Versioning:
    # No test for older major versions as that case is currently impossible with
    # 1.0 as the only possible version.

    def _example(self, major, minor):
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta name="pypi:repository-version" content="{major}.{minor}">
            </head>
            <body>
                <!-- This space intentionally left blank. -->
            </body>
        </html>
        """

    def test_unspecified(self, parser):
        html = """
        <!DOCTYPE html>
        <html>
            <body>
                <!-- This space intentionally left blank. -->
            </body>
        </html>
        """
        # No errors.
        parser(html)

    def test_equal(self, parser):
        html = self._example(*simple._SUPPORTED_VERSION)
        # No errors.
        parser(html)

    def test_newer_minor(self, parser):
        html = self._example(
            simple._SUPPORTED_VERSION[0], simple._SUPPORTED_VERSION[1] + 1
        )
        with warnings.catch_warnings(record=True) as raised_warnings:
            parser(html)

            assert raised_warnings and len(raised_warnings) == 1
            assert raised_warnings[0].category is simple.UnsupportedVersionWarning

    def test_newer_major(self, parser):
        html = self._example(simple._SUPPORTED_VERSION[0] + 1, 0)
        with pytest.raises(simple.UnsupportedVersion):
            parser(html)

    def test_older_minor(self, parser, monkeypatch):
        monkeypatch.setattr(simple, "_SUPPORTED_VERSION", (1, 1))
        html = self._example(1, 0)
        # No error.
        parser(html)


class TestPEP658Metadata:
    def test_default(self):
        html = '<a href="spam-1.2.3-py3.none.any.whl">spam-1.2.3-py3.none.any.whl</a>'
        archive_link = simple.parse_archive_links(html)[0]
        assert archive_link.metadata is None

    @pytest.mark.parametrize(
        "attribute", ["data-dist-info-metadata", "data-dist-info-metadata=true"]
    )
    def test_attribute_only(self, attribute):
        html = f'<a href="spam-1.2.3-py3.none.any.whl" {attribute} >spam-1.2.3-py3.none.any.whl</a>'
        archive_link = simple.parse_archive_links(html)[0]
        assert archive_link.metadata == ("", "")

    @pytest.mark.parametrize(
        "attribute",
        [
            'data-dist-info-metadata="sha256=abcdef"',
            'data-dist-info-metadata="SHA256=abcdef"',
        ],
    )
    def test_hash(self, attribute):
        html = f'<a href="spam-1.2.3-py3.none.any.whl" {attribute}>spam-1.2.3-py3.none.any.whl</a>'
        archive_link = simple.parse_archive_links(html)[0]
        assert archive_link.metadata == ("sha256", "abcdef")
