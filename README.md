# re-ai-scrap
Reasearch for scrapping web pages using LLM, implementing smart agents etc

## Running samples

### Prepare python env

#### init conda

```bash
conda create --name llm  python=3.11
conda activate llm
```

#### requirements
```bash
pip install -r requirements.txt
```

#### playwright
```bash
playwright install
```

### Langchain demo

Code: `egs/langchain/main.py`

#### Objective

https://github.com/xdeli-tech/xdeli-issues/issues/1975


```txt
Check out the latest 10 press releases published by companies on PR Newswire. Then, please send company information to this form https://forms.gle/f6ukAo2tkoNu5H7w7 to contact by our sales team.

PR newswire: https://www.prnewswire.com/
Form to correct company data: https://forms.gle/f6ukAo2tkoNu5H7w7
```

#### Running sample


```bash
export OPENAI_API_KEY=....

## take tha last 3 articles
make run/demo/langchain  params="--limit=3"

## demo caches all calls to web and llm
## clean cache
make clean/cache

## run with gpt-4
make run/demo/langchain params="--limit=3 --model=gpt-4-0125-preview --context=12000"

## submit form
make run/demo/langchain params="--limit=3 --model=gpt-4-0125-preview --context=12000 --submit_forms"

```
