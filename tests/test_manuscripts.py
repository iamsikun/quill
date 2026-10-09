from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest
import yaml

from quill.assembly import assemble_paper, camera_ready
from quill.cli import main
from quill.importer import import_paper
from quill.sync import init_project
from quill.validate import validate_repo
from quill.workspace import create_journal_version, new_paper, sync_context


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    init_project(root)
    return root


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    files = {
        'paper.tex': r'''\documentclass{article}
\usepackage{graphicx}
\graphicspath{{plots/}}
\begin{document}
\input{chapters/introduction}
\include{chapters/results}
See \ref{sec:results} and \citep{Source2024}.
\bibliographystyle{plainnat}
\bibliography{bib/references}
\end{document}
''',
        'chapters/introduction.tex': '\\section{Introduction}\n\\input{details/results}\n',
        'chapters/results.tex': '\\section{Results}\\label{sec:results}\n\\includegraphics{result}\n',
        'details/results.tex': 'Different file with the same basename.\n',
        'plots/result.pdf': 'synthetic figure bytes',
        'bib/references.bib': '@article{Source2024, title={Source}, author={A}, year={2024}}\n',
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def test_import_preserves_nested_dependencies_and_all_bytes(project, source):
    import_paper(project, source=source, title='Imported')
    target = project / 'paper/manuscript'
    for relative, payload in snapshot(source).items():
        assert (target / relative).read_bytes() == payload
    assert not (target / 'main.tex').exists()
    assert yaml.safe_load((target / 'target.yaml').read_text())['entrypoint'] == 'paper.tex'
    assert validate_repo(project).ok
    context = sync_context(project).read_text()
    assert 'chapters/introduction.tex' in context and 'details/results.tex' in context
    assert assemble_paper(project).read_bytes() == (source / 'paper.tex').read_bytes()


def test_monolithic_import_keeps_headings_preamble_and_document_boundaries(project, tmp_path):
    source = tmp_path / 'whole.tex'
    source.write_text('\\documentclass{article}\n\\newcommand{\\test}{Test}\n\\begin{document}\n'
                      '\\section{Introduction}\\test\n\\section{Discussion}Evidence.\n\\end{document}\n')
    import_paper(project, source=source, title='Imported')
    assert (project / 'paper/manuscript/whole.tex').read_bytes() == source.read_bytes()
    assert not list((project / 'paper/manuscript/sections').iterdir())


def test_creation_and_import_refuse_existing_target_without_any_changes(project, source):
    new_paper(project, title='Existing')
    context = project / 'paper/shared/context.md'
    context.write_text(context.read_text() + '\nPersonal decisions.\n')
    before = snapshot(project)
    with pytest.raises(ValueError, match='already exists'):
        new_paper(project, title='Replacement')
    assert snapshot(project) == before
    with pytest.raises(ValueError, match='already exists'):
        import_paper(project, source=source, title='Replacement')
    assert snapshot(project) == before


def test_second_target_preserves_shared_context_and_bibliography(project, source):
    new_paper(project, title='Existing')
    bibliography = project / 'paper/shared/references-master.bib'
    bibliography.write_text('@book{Personal, title={Keep}}')
    before = snapshot(project / 'paper/shared')
    import_paper(project, source=source, title='Other', target_name='other')
    assert snapshot(project / 'paper/shared') == before
    create_journal_version(project, venue_key='econometrica')
    before = snapshot(project)
    with pytest.raises(ValueError, match='already exists'):
        create_journal_version(project, venue_key='marketing-science')
    assert snapshot(project) == before


def test_packaging_preserves_manuscript_and_excludes_stale_files(project, source):
    import_paper(project, source=source, title='Imported', venue_key='neurips')
    target = project / 'paper/conference'
    archive = camera_ready(project)
    with zipfile.ZipFile(archive) as bundle:
        for relative, payload in snapshot(source).items():
            assert bundle.read(relative) == payload
        assert 'main.tex' not in bundle.namelist()  # template shell is never shipped
    (target / 'camera-ready/stale.txt').write_text('old submission')
    camera_ready(project)
    with zipfile.ZipFile(archive) as bundle:
        assert 'stale.txt' not in bundle.namelist()
    assert not (target / 'camera-ready/stale.txt').exists()


def test_package_failure_preserves_previous_archive_and_state(project):
    new_paper(project, title='Manuscript')
    assemble_paper(project)
    archive = camera_ready(project)
    before = archive.read_bytes()
    state = (project / 'paper/state.yaml').read_bytes()
    (project / 'paper/manuscript/main.tex').write_text('\\input{missing}')
    with pytest.raises(ValueError, match='missing input'):
        camera_ready(project)
    assert archive.read_bytes() == before
    assert (project / 'paper/state.yaml').read_bytes() == state


def test_failed_implicit_assembly_does_not_advance_target_stage(project):
    new_paper(project, title='Manuscript')
    (project / 'paper/manuscript/sections/introduction.tex').write_text('\\ref{missing}')
    state = (project / 'paper/state.yaml').read_bytes()
    with pytest.raises(ValueError, match='undefined reference'):
        camera_ready(project)
    assert (project / 'paper/state.yaml').read_bytes() == state


def test_validate_reports_dependencies_and_reference_keys(project):
    new_paper(project, title='Test')
    (project / 'paper/manuscript/main.tex').write_text(
        '\\input{absent}\n\\includegraphics{missing-figure}\n\\bibliography{missing-bib}\n'
        '\\ref{unknown} \\citep{Unknown2024}\n')
    result = validate_repo(project)
    assert not result.ok
    for expected in ('missing input', 'missing includegraphics', 'missing bibliography', 'undefined reference', 'undefined citation'):
        assert any(expected in error for error in result.errors)


def test_validation_uses_one_document_graph_and_ignores_comments(project):
    for name in ('one', 'two'):
        new_paper(project, title=name, target_name=name)
        target = project / 'paper' / name
        (target / 'main.tex').write_text('\\label{same}\\ref{same}\n% \\input{missing} \\cite{??}\n'
                                       '\\begin{verbatim}\\ref{example}\\end{verbatim}\n')
        (target / 'sections/unused.tex').write_text('\\ref{not-in-the-document}')
    assert validate_repo(project).ok
    (project / 'paper/two/main.tex').write_text('\\ref{bad}')
    assert validate_repo(project, target_name='one').ok
    assert not validate_repo(project, target_name='two').ok


@pytest.mark.parametrize('text', ['\\input{missing}', '\\input{\\dynamic}', '\\input{../outside}'])
def test_import_failure_does_not_create_workspace(project, tmp_path, text):
    source = tmp_path / 'bad.tex'
    source.write_text(text)
    before = snapshot(project)
    with pytest.raises(ValueError):
        import_paper(project, source=source, title='Broken')
    assert snapshot(project) == before


def test_ambiguous_import_requires_explicit_entrypoint(project, tmp_path):
    source = tmp_path / 'sources'
    source.mkdir()
    for filename in ('paper.tex', 'response.tex'):
        (source / filename).write_text('\\documentclass{article}')
    with pytest.raises(ValueError, match='exact .tex file'):
        import_paper(project, source=source, title='Ambiguous')
    assert not (project / 'paper').exists()


def test_generic_cli_needs_only_title(project, monkeypatch):
    monkeypatch.chdir(project)
    with pytest.raises(SystemExit) as stopped:
        main(['new-paper', '--title', 'Early draft'])
    assert stopped.value.code == 0
    metadata = yaml.safe_load((project / 'paper/manuscript/target.yaml').read_text())
    assert metadata['venue'] == 'generic'
    assert metadata['bibstyle'] == 'plainnat'
    assert metadata['title'] == 'Early draft'


@pytest.mark.skipif(shutil.which('pdflatex') is None, reason='requires a TeX installation')
def test_generic_package_compiles_from_extracted_archive(project, tmp_path):
    from quill.assembly import _run_latex_sequence
    new_paper(project, title='Portable manuscript')
    section = project / 'paper/manuscript/sections/introduction.tex'
    section.write_text('\\section{Introduction}\\label{sec:intro}\nSee Section~\\ref{sec:intro}.\n')
    assemble_paper(project, compile_pdf=True)
    archive = camera_ready(project, compile_pdf=True)
    extracted = tmp_path / 'extracted'
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extracted)
    (extracted / 'main.pdf').unlink()
    _run_latex_sequence(extracted)
    assert (extracted / 'main.pdf').is_file()


@pytest.mark.skipif(shutil.which('pdflatex') is None, reason='requires a TeX installation')
def test_imported_entrypoint_and_bibliography_compile_from_archive(project, tmp_path):
    from quill.assembly import _run_latex_sequence
    source = tmp_path / 'nested-source'
    files = {
        'src/paper.tex': '\\documentclass{article}\n\\usepackage{natbib,local}\n\\begin{document}\n'
                         '\\input{sections/intro}\n\\bibliographystyle{plainnat}\n'
                         '\\bibliography{bib/paper}\n\\end{document}\n',
        'sections/intro.tex': '\\section{Introduction}\\label{sec:intro}\n'
                              '\\studyword{} from \\citet{Author2024}; see \\ref{sec:intro}.\n',
        'local.sty': '\\ProvidesPackage{local}\n\\newcommand{\\studyword}{Evidence}\n',
        'bib/paper.bib': '@article{Author2024, author={Author, A.}, title={Evidence}, journal={Journal}, year={2024}}\n',
    }
    for relative, text in files.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    import_paper(project, source=source / 'src/paper.tex', source_root=source, title='Imported')
    archive = camera_ready(project, compile_pdf=True)
    extracted = tmp_path / 'extracted-import'
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extracted)
    (extracted / 'paper.pdf').unlink()
    _run_latex_sequence(extracted, 'src/paper.tex')
    assert (extracted / 'paper.pdf').is_file()
    for relative, text in files.items():
        assert (extracted / relative).read_text() == text
