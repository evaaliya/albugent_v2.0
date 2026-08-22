#for env

source $HOME/.local/bin/env

uv venv --python 3.11

source .venv/bin/activate

uv pip install -r requirements.txt              #or
uv pip install -r agent/requirements.txt

#для сброса всего и рестарта docker
docker compose down --remove-orphans
docker compose build --no-cache && docker compose run --rm strands-agent

#github commands
git status

git add .

git commit -m "feat: complete initial setup for Strands Agent and MCP integration"
git push origin main

#если были внесены изменения через интерфейс
git pull origin main --rebase

git push origin main

или
git push origin main --force-with-lease
(Флаг --force-with-lease — это безопасный аналог force push: он обновит ветку, но защитит тебя, если на GitHub вдруг появился какой-то другой чужой код).


git add .gitignore README.md
git commit -m "docs: fix README markdown formatting"
git push origin main

3. Удали ⁠.db⁠ файлы из отслеживания Git (без удаления с компьютера)
Выполни в терминале команду, которая уберет уже закоммиченные базы из индекса Git, но сохранит их у тебя на диске:

git rm --cached data/**/*.db
git commit -m "chore: remove heavy sqlite databases from git tracking"
git push origin main

### For README.md

### 2. Run with Docker Compose
Build and launch the agent environment in interactive mode:

```bash
docker compose run --build --rm strands-agent
docker-compose down

*(Обрати внимание на закрывающие ` ``` ` на строке перед `## 📋 Architecture Overview`!)*

---

### 2. Как удалить `comands.md` с GitHub (сохранив его на Mac)

Судя по терминалу на первом скриншоте, ты сделала `git push`, но файл `comands.md` все еще висит в Git.

Выполни по очереди эти 3 команды в терминале внизу VS Code:

**Шаг 1. Добавь имя файла в конец `.gitignore`** *(если еще не добавила)*.

**Шаг 2. Убери файл из индекса Git:**
```bash
git rm --cached comands.md
Шаг 3. Закоммить и запушь:

Bash
git add .gitignore README.md
git commit -m "docs: fix README markdown formatting and ignore personal cheat sheet"
git push origin main




Шаг 1. Создаём .gitignore
В корневой директории проекта (albugent_v2.0) создай файл .gitignore и внеси в него все чувствительные файлы и системные артефакты:

Фрагмент кода
# Переменные окружения и секреты (КРИТИЧНО)
.env
*.env
.env.*
!.env.example

# Кеш Python и артефакты
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Настройки VS Code / IDE
.vscode/
.idea/
*.swp
*.swo

# MacOS системные файлы
.DS_Store

# Кеш Docker / тестирования
.pytest_cache/
.coverage
htmlcov/
Обрати внимание: Если твой файл с переменными окружения называется .env, убедись, что он точно внесен в .gitignore перед добавлением файлов в индекс Git.

Шаг 2. Проверяем шаблон .env.example
Для того чтобы проект оставался воспроизводимым для других или для CI/CD, создай файл .env.example с пустыми значениями (шаблоном):

Фрагмент кода
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
GITHUB_TOKEN=your_github_token
GITHUB_REPOSITORY=owner/repo
Шаг 3. Безопасная индексация и проверкa
Открой терминал в папке проекта и выполни последовательно:

1. Проверяем статус и скрытые файлы
Bash
git status
Проверка: В списке Untracked files не должно быть файла .env с твоими реальными ключами. В списке должен быть .gitignore, .env.example и исходный код.

2. Добавляем файлы в индекс
Bash
git add .
3. Проверяем, что попало в стейджинг (финальный контроль)
Bash
git status
Если случайно добавился .env (он подсвечен зеленым), немедленно суппорти его из индекса:

Bash
git rm --cached .env
Шаг 4. Коммит и Пуш
Когда убедилась, что секреты не попали в список изменений:

Bash
git commit -m "feat: complete initial setup for Strands Agent and MCP integration"
git push origin main
(замени main на имя своей ветки, если работаешь в другой).

### pii-detector.py
import time
from typing import List, Dict, Any

PII_KEYWORDS = ["name", "ssn", "passport", "email", "patient", "driver", "credit_card", "license"]

def evaluate_dataset_risk(
    urn: str,
    fields: List[str],
    centrality: float,
    is_orphan: bool,
    last_updated_ts: float = 0.0
) -> Dict[str, Any]:
    """
    Рассчитывает комбинированный риск датасета (PII + свежесть + связность + сирота).
    """
    pii_fields = [f for f in fields if any(kw in f.lower() for kw in PII_KEYWORDS)]
    has_pii = len(pii_fields) > 0

    hours_stale = 0.0
    has_freshness_issue = False
    if last_updated_ts > 0:
        hours_stale = (time.time() - (last_updated_ts / 1000.0)) / 3600.0
        if hours_stale > 24.0:
            has_freshness_issue = True

    # Формула взвешенного риска
    risk_score = min(
        1.0,
        (0.4 * centrality) + 
        (0.4 if has_pii else 0.0) + 
        (0.2 if is_orphan else 0.0) + 
        (0.1 if has_freshness_issue else 0.0)
    )

    return {
        "urn": urn,
        "risk_score": round(risk_score, 3),
        "has_pii": has_pii,
        "pii_fields": pii_fields,
        "is_orphan": is_orphan,
        "has_freshness_issue": has_freshness_issue,
        "hours_stale": round(hours_stale, 1)
    }










data/**/*.db
data/**/*.csv
*.db
*.db
data/**/*.csv
*.sqlite
*.sqlite3






# Step 4: Запускаем ПОЛНЫЙ цикл Агента (MCP Scan + Bedrock Reasoning + Draft PR)
      - name: Execute Albugent Autonomous Workflow
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: ${{ secrets.AWS_REGION }}
          AWS_BEDROCK_MODEL_ID: ${{ secrets.AWS_BEDROCK_MODEL_ID }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          docker compose run --rm \
            -e AWS_ACCESS_KEY_ID \
            -e AWS_SECRET_ACCESS_KEY \
            -e AWS_REGION \
            -e AWS_BEDROCK_MODEL_ID \
            -e GITHUB_TOKEN \
            -e GITHUB_REPOSITORY \
            strands-agent bash -c "
             python data/healthcare/create_db.py && \
             python data/nyc-taxi/create_db.py && \
             python data/fiction-retail/create_db.py && \
             python agent/agent.py
            "










albugent_v2.0/
|__.github
|__.venv
|________________________________________agent/
|                                           |____prompts/
|___context_builder/                        |.        |_____init__.py
|               |____init__.py              |         |______system_prompts.py
|               |__context_builder.py       |____agent.py
|___docs/                                   |____dockerfile
|                                           |____req.txt                                             
|
|__data/
|     |__healthcare
|.    |__fiction_retail
|.    |__nyc_taxi
|
|___mcp_server/
|.          |__pycache__
|.          |__init__.py
|           |__dockerfile
|           |__mcp_server.py
|           |__req.txt
|.          |__utils/
|                 |__pycache__
|                 |__init__.py
|                 |__db_utils.py
|                 |__graph_engine.py
|                 |__lineage_discoverer.py
|                 |__pii_detector.py
|__scripts/
|__.env
|__
|__.env.example
|__.gitignore
|__commands.md
|__docker-compose.yaml
|__LICENSE
|README.MD
|

























||