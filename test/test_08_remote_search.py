
import pytest
from test import TEST_REF, TEST_REF_OFFICIAL, TEST_REMOTE_NAME
from test.conan_helper import conan_install_ref, conan_remove_ref

from conan_unified_api.types import ConanRef
from conan_unified_api.unified_api import ConanUnifiedApi


def test_info_simple(conan_api: ConanUnifiedApi):
    # ref needs to be in a remote
    info = conan_api.info(TEST_REF_OFFICIAL)
    assert len(info) == 1
    assert info[0].get("binary_remote") == "local"
    assert info[0].get("reference") == TEST_REF_OFFICIAL.split("@")[0]


def test_info_transitive_reqs(conan_api: ConanUnifiedApi):
    info = conan_api.info("nocompsettings/1.0.0@local/no_sets")
    assert len(info) == 2
    assert info[0].get("binary_remote") == TEST_REMOTE_NAME
    assert info[0].get("reference") == "nocompsettings/1.0.0@local/no_sets"

    assert info[1].get("reference") == TEST_REF

def test_conan_find_remote_pkg(conan_api: ConanUnifiedApi):
    """
    Test, if search_package_in_remotes finds a package for the current system and the specified options.
    The function must find exactly one pacakge, which uses the spec. options and corresponds to the
    default settings.
    """
    conan_remove_ref(TEST_REF)
    default_settings = conan_api.get_default_settings()

    pkgs, remote = conan_api.find_best_matching_package_in_remotes(ConanRef.loads(TEST_REF),
                                                        {"shared": "True"})
    assert remote == TEST_REMOTE_NAME
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert {"shared": "True"}.items() <= pkg.get("options", {}).items()

    for setting in default_settings:
        if setting in pkg.get("settings", {}).keys():
            if "compiler." in setting: # don't evaluate comp. details
                continue
            assert default_settings[setting] in pkg.get("settings", {})[setting]


def test_conan_not_find_remote_pkg_wrong_opts(conan_api: ConanUnifiedApi):
    """
    Test, if a wrong Option return causes an error.
    Empty list must be returned and the error be logged.
    """
    conan_remove_ref(TEST_REF)
    pkg, remote = conan_api.find_best_matching_package_in_remotes(ConanRef.loads(TEST_REF),
                                                      {"BogusOption": "True"})
    assert not pkg


def test_conan_find_local_pkg(conan_api: ConanUnifiedApi):
    """
    Test, if get_package installs the package and returns the path and check it again.
    The bin dir in the package must exist (indicating it was correctly downloaded)
    """
    conan_remove_ref(TEST_REF)
    conan_install_ref(TEST_REF)
    pkgs = conan_api.find_best_matching_packages(ConanRef.loads(TEST_REF))
    assert len(pkgs) == 1 # default options are filtered

# @pytest.mark.conanv2 TODO create package for it


def test_compiler_no_settings(conan_api: ConanUnifiedApi, capfd):
    """
    Test, if a package with no settings at all can install
    The actual installaton must not return an error.
    """
    ref = "nocompsettings/1.0.0@local/no_sets"
    conan_remove_ref(ref)
    capfd.readouterr() # remove can result in error message - clear

    id, package_folder = conan_api.get_path_or_auto_install(ConanRef.loads(ref))
    assert (package_folder / "bin").is_dir()
    captured = capfd.readouterr()
    assert "ERROR" not in captured.err
    assert "Can't find a matching package" not in captured.err
    conan_remove_ref(ref)


def test_search_for_all_packages(conan_api: ConanUnifiedApi):
    """ Test, that an existing ref will be found in the remotes. """
    res = conan_api.search_recipe_all_versions_in_remotes(ConanRef.loads(TEST_REF))
    ref = ConanRef.loads(TEST_REF)  # need to convert @_/_
    assert str(ref) in str(res)
