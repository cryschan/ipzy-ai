"""
배경 제거 API 성능 비교 테스트
개별 API vs 배치 API 처리 시간 측정
"""
import httpx
import asyncio
import time
from typing import List

BASE_URL = "http://localhost:8000/api/image"

# 테스트용 이미지 URL (실제 무신사 상품)
TEST_URLS = [
    "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20251021/5622113/5622113_17621339011392_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20250912/5453617/5453617_17593914818524_big.jpg",
    "https://image.msscdn.net/thumbnails/images/prd_img/20251110/5706908/detail_5706908_17645684586675_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20251202/5797228/5797228_17648344633914_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20250929/5545402/5545402_17658423534526_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20251106/5695144/5695144_17630033769943_big.jpg",
    "https://image.msscdn.net/thumbnails/images/goods_img/20251014/5588847/5588847_17617928490931_big.png",
    "https://image.msscdn.net/thumbnails/images/prd_img/20251111/5717317/detail_5717317_17628569317535_big.jpg",
]


async def call_individual_api_with_retry(client: httpx.AsyncClient, url: str, index: int, max_retries: int = 2) -> tuple:
    """
    개별 API 호출 (재시도 로직 포함)

    Args:
        client: httpx AsyncClient
        url: 이미지 URL
        index: 인덱스 (출력용)
        max_retries: 최대 재시도 횟수

    Returns:
        (index, success, response_or_error)
    """
    for attempt in range(max_retries + 1):
        try:
            response = await client.post(
                f"{BASE_URL}/remove-background",
                json={"image_url": url}
            )
            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                retry_msg = f" (재시도 {attempt}회)" if attempt > 0 else ""
                return (index, True, result, retry_msg)
            else:
                error_msg = result.get('message', 'Unknown error')
                if attempt < max_retries:
                    print(f"  [{index+1}] ⚠️  실패 (재시도 {attempt+1}/{max_retries}): {error_msg}")
                    await asyncio.sleep(1)  # 1초 대기 후 재시도
                    continue
                return (index, False, error_msg, "")

        except httpx.TimeoutException as e:
            if attempt < max_retries:
                print(f"  [{index+1}] ⚠️  타임아웃 (재시도 {attempt+1}/{max_retries})")
                await asyncio.sleep(1)
                continue
            return (index, False, f"타임아웃 (60초 초과)", "")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if attempt < max_retries:
                print(f"  [{index+1}] ⚠️  {error_msg} (재시도 {attempt+1}/{max_retries})")
                await asyncio.sleep(1)
                continue
            return (index, False, error_msg, "")

        except Exception as e:
            error_msg = f"예외: {type(e).__name__}: {str(e)}"
            if attempt < max_retries:
                print(f"  [{index+1}] ⚠️  {error_msg} (재시도 {attempt+1}/{max_retries})")
                await asyncio.sleep(1)
                continue
            return (index, False, error_msg, "")

    return (index, False, "최대 재시도 횟수 초과", "")


async def test_individual_api(urls: List[str]) -> dict:
    """개별 API를 여러 번 호출 (병렬 처리 + 재시도)"""
    print("\n" + "="*60)
    print("🔴 개별 API 테스트 (10번 호출, 병렬 처리, 재시도 포함)")
    print("="*60)

    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:  # 타임아웃 60초로 증가
        tasks = []
        for i, url in enumerate(urls):
            task = call_individual_api_with_retry(client, url, i, max_retries=2)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    # 결과 분석 및 출력
    success_count = 0
    failed_count = 0

    for index, success, data, retry_msg in results:
        if success:
            print(f"  [{index+1}] ✅ 성공{retry_msg}")
            success_count += 1
        else:
            print(f"  [{index+1}] ❌ 실패: {data}")
            failed_count += 1

    print(f"\n📊 결과:")
    print(f"  - 총 요청: {len(urls)}개")
    print(f"  - 성공: {success_count}개")
    print(f"  - 실패: {failed_count}개")
    print(f"  - 총 소요 시간: {total_time:.2f}초")
    print(f"  - 평균 처리 시간: {total_time/len(urls):.2f}초/개")

    return {
        'method': 'individual',
        'total_time': total_time,
        'success_count': success_count,
        'failed_count': failed_count,
        'avg_time': total_time / len(urls)
    }


async def test_batch_api(urls: List[str]) -> dict:
    """배치 API로 한 번에 처리"""
    print("\n" + "="*60)
    print("🟢 배치 API 테스트 (1번 호출)")
    print("="*60)

    start_time = time.time()

    async with httpx.AsyncClient(timeout=180.0) as client:  # 타임아웃 180초 (3분)
        response = await client.post(
            f"{BASE_URL}/remove-background/batch",
            json={"image_urls": urls}
        )

    end_time = time.time()
    total_time = end_time - start_time

    result = response.json()

    # 결과 출력
    for i, item in enumerate(result.get('results', [])):
        if item['success']:
            print(f"  [{i+1}] ✅ 성공")
        else:
            print(f"  [{i+1}] ❌ 실패: {item.get('error')}")

    print(f"\n📊 결과:")
    print(f"  - 총 요청: {result.get('total_count')}개")
    print(f"  - 성공: {result.get('success_count')}개")
    print(f"  - 실패: {result.get('failed_count')}개")
    print(f"  - API 보고 처리 시간: {result.get('processing_time')}초")
    print(f"  - 실제 왕복 시간: {total_time:.2f}초")
    print(f"  - 네트워크 오버헤드: {total_time - result.get('processing_time', 0):.2f}초")

    return {
        'method': 'batch',
        'total_time': total_time,
        'processing_time': result.get('processing_time'),
        'success_count': result.get('success_count'),
        'failed_count': result.get('failed_count'),
        'avg_time': result.get('processing_time', 0) / result.get('total_count', 1)
    }


async def main():
    print("\n" + "🚀 배경 제거 API 성능 비교 테스트 (개선된 배치 API)")
    print(f"테스트 이미지 개수: {len(TEST_URLS)}개\n")

    # 배치 API 테스트 (먼저 실행 - 타임아웃 개선 확인)
    batch_result = await test_batch_api(TEST_URLS)

    # 잠시 대기 (서버 부하 분산)
    print("\n⏳ 5초 대기 중...")
    await asyncio.sleep(5)

    # 개별 API 테스트
    individual_result = await test_individual_api(TEST_URLS)

    # 비교 결과
    print("\n" + "="*60)
    print("📈 성능 비교 결과")
    print("="*60)

    time_saved = individual_result['total_time'] - batch_result['total_time']
    improvement = (time_saved / individual_result['total_time']) * 100

    print(f"\n개별 API (10번 호출):")
    print(f"  ├─ 총 소요 시간: {individual_result['total_time']:.2f}초")
    print(f"  ├─ 성공/실패: {individual_result['success_count']}/{individual_result['failed_count']}")
    print(f"  └─ 평균 처리 시간: {individual_result['avg_time']:.2f}초/개")

    print(f"\n배치 API (1번 호출):")
    print(f"  ├─ 총 소요 시간: {batch_result['total_time']:.2f}초")
    print(f"  ├─ 성공/실패: {batch_result['success_count']}/{batch_result['failed_count']}")
    print(f"  └─ 평균 처리 시간: {batch_result['avg_time']:.2f}초/개")

    print(f"\n⚡ 성능 개선:")
    if time_saved > 0:
        print(f"  ├─ 절약된 시간: {time_saved:.2f}초")
        print(f"  └─ 개선율: {improvement:.1f}% 빠름")
    else:
        print(f"  └─ 개별 API가 더 빠름 (차이: {abs(time_saved):.2f}초)")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
