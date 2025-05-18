import requests
from bs4 import BeautifulSoup
import json

# 크롤링할 페이지들
URLS = [
    "https://www.kead.or.kr/edsysdesc/cntntsPage.do?menuId=MENU0684",
    "https://www.kead.or.kr/edhowapply/cntntsPage.do?menuId=MENU0686",
    "https://www.kead.or.kr/edclcmth/cntntsPage.do?menuId=MENU0687",
    "https://www.kead.or.kr/edfrdlbnft/cntntsPage.do?menuId=MENU0688",
    "https://www.kead.or.kr/edformlbrry/cntntsPage.do?menuId=MENU0689",
    "https://www.kead.or.kr/bbs/faq/bbsPage.do?adt1Code=002&menuId=MENU0691",
    "https://www.kead.or.kr/bbs/faq/bbsPage.do?pageIndex=2&bbsCode=faq&bbsCnId=&bbsNm=%EC%A7%88%EB%AC%B8%EA%B3%BC+%EB%8B%B5%EB%B3%80&menuId=MENU0691&adt1Code=002&adt2Code=&searchCondition=sjcn&searchKeyword=&recordCountPerPage=10",
    "https://www.kead.or.kr/bbs/faq/bbsPage.do?pageIndex=3&bbsCode=faq&bbsCnId=&bbsNm=%EC%A7%88%EB%AC%B8%EA%B3%BC+%EB%8B%B5%EB%B3%80&menuId=MENU0691&adt1Code=002&adt2Code=&searchCondition=sjcn&searchKeyword=&recordCountPerPage=10",
    "https://www.kead.or.kr/nptsysdesc/cntntsPage.do?menuId=MENU0899",
    "https://www.kead.or.kr/ndthowapply/cntntsPage.do?menuId=MENU0900",
    "https://www.kead.or.kr/emplymncst/cntntsPage.do?menuId=MENU0666",
    "https://www.kead.or.kr/ffssysdesc/cntntsPage.do?menuId=MENU0701",
    "https://www.kead.or.kr/bbs/faq/bbsPage.do?adt1Code=007&menuId=MENU0702",
    "https://www.kead.or.kr/emplyobsys/cntntsPage.do?menuId=MENU0648",
    "https://www.kead.or.kr/spremoblgt/cntntsPage.do?menuId=MENU0649",
    "https://www.kead.or.kr/epstempemppln/cntntsPage.do?menuId=MENU0651",
    "https://www.kead.or.kr/epstcvlstempln/cntntsPage.do?menuId=MENU0652",
    "https://www.kead.or.kr/emplfsysdsc/cntntsPage.do?menuId=MENU0654",
    "https://www.kead.or.kr/emplfeycpcds/cntntsPage.do?menuId=MENU0655",
    "https://www.kead.or.kr/bbs/faq/bbsPage.do?adt1Code=011&menuId=MENU0656"
]

# 🔹 표 내용 추출
def extract_table_texts(content_area):
    tables = content_area.find_all("table")
    table_texts = []

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
            if cols:
                table_texts.append(" | ".join(cols))

    return table_texts

# 🔹 FAQ (아코디언 포함) 추출 통합 함수
def extract_accordion_faqs(soup):
    faq_lines = []

    # ✅ 기존 구조 (ul.faq_list, dl.faq)
    faq_items = soup.select("ul.faq_list li") or soup.select("dl.faq dt")
    for item in faq_items:
        question = item.select_one("a, dt")
        answer = item.find_next_sibling("dd") or item.select_one("div.answer, dd")
        if question and answer:
            q = question.get_text(strip=True)
            a = answer.get_text(strip=True)
            faq_lines.append(f"Q: {q}\nA: {a}")

    # ✅ 추가: board_qa 아코디언 구조
    board_qa = soup.select("dl.board_qa dt")
    for dt in board_qa:
        button = dt.select_one("button")
        dd = dt.find_next_sibling("dd")
        if button and dd:
            q = button.get_text(strip=True).replace("Q", "").strip()
            a = dd.get_text(strip=True)
            faq_lines.append(f"Q: {q}\nA: {a}")

    return faq_lines

# 🔹 카테고리 자동 분류
def classify_category(title: str, body: str, url: str) -> str:
    lower_title = title.lower()
    lower_body = body.lower()

    # ✅ FAQ 우선 처리
    if "faq" in url or "자주 묻는 질문" in body or "Q:" in body:
        return "FAQ"

    # ✅ 지원금/지원제도 먼저 체크
    if any(keyword in lower_title + lower_body for keyword in ["장려금", "지원금", "지급단가", "임금지원", "신규고용"]):
        return "지원금"
    if any(keyword in lower_title + lower_body for keyword in ["무상지원", "근로지원비용", "작업장비", "편의시설", "작업지도원", "재택근무"]):
        return "지원제도"

    # ✅ 의무제도 (지원이 없고 의무만 강조된 경우만 해당)
    if any(keyword in lower_body for keyword in ["의무고용률", "의무고용", "고용의무", "고용률 초과", "고용률 미달"]):
        return "의무제도"

    # ✅ 부담금
    if any(keyword in lower_body for keyword in ["부담금", "징수", "환수", "제재", "벌칙"]):
        return "부담금"

    return "기타"

# 🔹 한 페이지 처리
def fetch_policy(url: str):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.title.string.strip()

    # 📌 FAQ 전용 페이지 처리 분기
    if "bbs/faq" in url:
        faq_lines = extract_accordion_faqs(soup)
        if not faq_lines:
            raise ValueError(f"[❌] FAQ 내용 없음: {url}")
        body = "\n[자주 묻는 질문]\n" + "\n".join(faq_lines)
        category = classify_category(title, body, url)
        return {
            "title": title,
            "body": body,
            "category": category,
            "url": url,
            "embedding": None
        }

    # 📌 일반 콘텐츠 페이지
    content_area = (
        soup.select_one("main#main_content article.content_width div.body.text") or
        soup.find("div", id="body_text") or
        soup.find("div", class_="body_text")
    )
    if not content_area:
        raise ValueError(f"[❌] 본문 영역 없음: {url}")

    # 본문 추출 (data-brl-use 우선)
    brl_elements = content_area.find_all(attrs={"data-brl-use": True})
    lines = [el.get_text(strip=True) for el in brl_elements if el.get_text(strip=True)]

    if not lines:
        lines = [tag.get_text(strip=True) for tag in content_area.find_all(["p", "div", "li", "span", "h4"]) if tag.get_text(strip=True)]

    # 표
    table_lines = extract_table_texts(content_area)
    if table_lines:
        lines.append("\n[표 정보]")
        lines.extend(table_lines)

    # FAQ
    faq_lines = extract_accordion_faqs(soup)
    if faq_lines:
        lines.append("\n[자주 묻는 질문]")
        lines.extend(faq_lines)

    # 본문 구성
    body = "\n".join(lines)
    category = classify_category(title, body, url)

    return {
        "title": title,
        "body": body,
        "category": category,
        "url": url,
        "embedding": None
    }

# 🔹 실행
if __name__ == "__main__":
    all_docs = []

    for url in URLS:
        try:
            doc = fetch_policy(url)
            all_docs.append(doc)
            print(f"✅ 크롤링 완료: {url} ({len(doc['body'])}자)")
        except Exception as e:
            print(f"❌ 에러 발생: {url} → {e}")

    with open("scripts/policies.json", "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    print(f"📦 총 {len(all_docs)}건 저장됨 → scripts/policies.json")