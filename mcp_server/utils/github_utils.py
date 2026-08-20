import os
import secrets
from github import Github, GithubException

def create_remediation_pr(
    repo_name: str,
    pr_title: str,
    pr_body_markdown: str,
    remediation_file_path: str,
    remediation_sql_code: str,
    base_branch: str = "main"
) -> str:
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub Token is missing in environment variables!")

    g = Github(token)
    repo = g.get_repo(repo_name)

    # 1. Генерируем уникальное имя ветки для фикса
    branch_name = f"albugent/remediation-{secrets.token_hex(3)}"
    main_ref = repo.get_git_ref(f"heads/{base_branch}")
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)

    # 2. Создаем или обновляем SQL файл во вкладке Files Changed
    try:
        contents = repo.get_contents(remediation_file_path, ref=branch_name)
        repo.update_file(
            path=remediation_file_path,
            message=f"fix(governance): update automated cleansing rules in {remediation_file_path}",
            content=remediation_sql_code,
            sha=contents.sha,
            branch=branch_name
        )
    except GithubException:
        repo.create_file(
            path=remediation_file_path,
            message=f"fix(governance): create automated cleansing rules in {remediation_file_path}",
            content=remediation_sql_code,
            branch=branch_name
        )

    # 3. Открываем Draft PR (HITL Review Pattern)
    pr = repo.create_pull(
        title=pr_title,
        body=pr_body_markdown,
        head=branch_name,
        base=base_branch,
        draft=True
    )

    # 4. Навешиваем служебные метки
    try:
        pr.add_to_labels("awaiting-approval", "dataops-remediation")
    except Exception:
        pass

    return pr.html_url