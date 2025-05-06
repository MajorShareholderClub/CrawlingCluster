from crawling.src.driver.google.google_selenium import (
    GoogleSeleniumMovingElementLocation,
)


def test_google_crawler():
    print("Google 크롤러 테스트 시작")
    # 직접 인스턴스 생성
    crawler = GoogleSeleniumMovingElementLocation("BTC", 1)
    try:
        result = crawler.google_seleium_start()
        print(f"결과: {len(result) if result else 0}개의 항목 수집")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        print("테스트 종료")


if __name__ == "__main__":
    test_google_crawler()
