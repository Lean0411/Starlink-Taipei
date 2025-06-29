"""
命令列介面 - 薄介面層
"""
import asyncio
import argparse
from datetime import datetime
import json
from pathlib import Path

from ...infrastructure.container.container import get_container
from ...application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from ...application.dto.coverage_request import CoverageRequest


def create_parser() -> argparse.ArgumentParser:
    """創建命令列解析器"""
    parser = argparse.ArgumentParser(
        description="Starlink 衛星覆蓋率分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 位置參數
    parser.add_argument(
        "--lat", 
        type=float, 
        default=25.0330,
        help="觀測者緯度（預設：台北）"
    )
    parser.add_argument(
        "--lon", 
        type=float, 
        default=121.5654,
        help="觀測者經度（預設：台北）"
    )
    parser.add_argument(
        "--elevation", 
        type=float, 
        default=10.0,
        help="觀測者高度，公尺（預設：10）"
    )
    
    # 時間參數
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60,
        help="分析持續時間，分鐘（預設：60）"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=1,
        help="時間間隔，分鐘（預設：1）"
    )
    parser.add_argument(
        "--start-time",
        type=str,
        help="開始時間（ISO格式），預設為現在"
    )
    
    # 篩選參數
    parser.add_argument(
        "--min-elevation", 
        type=float, 
        default=25.0,
        help="最小仰角，度（預設：25）"
    )
    parser.add_argument(
        "--satellite-filter",
        type=str,
        help="衛星名稱篩選（支援通配符）"
    )
    
    # 輸出參數
    parser.add_argument(
        "--output",
        type=str,
        help="輸出檔案路徑"
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="summary",
        help="輸出格式（預設：summary）"
    )
    
    return parser


async def main():
    """主函數"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 解析開始時間
    if args.start_time:
        start_time = datetime.fromisoformat(args.start_time)
    else:
        start_time = datetime.now()
    
    # 創建請求
    request = CoverageRequest(
        observer_latitude=args.lat,
        observer_longitude=args.lon,
        observer_elevation=args.elevation,
        start_time=start_time,
        duration_minutes=args.duration,
        interval_minutes=args.interval,
        min_elevation=args.min_elevation,
        satellite_filter=args.satellite_filter
    )
    
    print(f"🛰️  Starlink 衛星覆蓋率分析")
    print(f"📍 位置: {args.lat:.4f}°N, {args.lon:.4f}°E")
    print(f"🕐 時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (持續 {args.duration} 分鐘)")
    print(f"📐 最小仰角: {args.min_elevation}°")
    
    if args.satellite_filter:
        print(f"🔍 衛星篩選: {args.satellite_filter}")
    
    print("\n正在分析...")
    
    try:
        # 獲取用例並執行
        container = get_container()
        use_case = container.resolve(AnalyzeCoverageUseCase)
        result = await use_case.execute(request)
        
        # 輸出結果
        if args.format == "summary":
            print_summary(result)
        else:
            print_json(result, args.output)
        
        # 儲存到檔案
        if args.output:
            save_result(result, args.output)
            print(f"\n💾 結果已儲存到: {args.output}")
    
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return 1
    
    return 0


def print_summary(result):
    """列印摘要"""
    stats = result.statistics
    
    print("\n📊 分析結果摘要:")
    print(f"├─ 分析 ID: {result.coverage_id}")
    print(f"├─ 時間範圍: {result.start_time} 至 {result.end_time}")
    print(f"├─ 總快照數: {stats.total_snapshots}")
    print(f"├─ 平均可見衛星數: {stats.average_visible_count:.1f}")
    print(f"├─ 最大可見衛星數: {stats.max_visible_count}")
    print(f"├─ 最小可見衛星數: {stats.min_visible_count}")
    print(f"└─ 覆蓋率: {stats.coverage_percentage:.1f}%")
    
    if result.optimal_windows:
        print("\n🌟 最佳觀測窗口:")
        for i, window in enumerate(result.optimal_windows[:3], 1):
            print(f"{i}. {window['start_time']} - {window['end_time']}")
            print(f"   持續: {window['duration_minutes']} 分鐘")
            print(f"   平均衛星數: {window['avg_satellites']:.1f}")


def print_json(result, output_path):
    """列印 JSON 格式"""
    data = {
        "coverage_id": result.coverage_id,
        "observer": result.observer,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "statistics": {
            "duration_minutes": result.statistics.duration_minutes,
            "average_visible_count": result.statistics.average_visible_count,
            "max_visible_count": result.statistics.max_visible_count,
            "min_visible_count": result.statistics.min_visible_count,
            "coverage_percentage": result.statistics.coverage_percentage,
            "total_snapshots": result.statistics.total_snapshots
        },
        "optimal_windows": result.optimal_windows,
        "snapshots": [
            {
                "timestamp": snapshot.timestamp,
                "visible_count": snapshot.visible_count,
                "max_elevation": snapshot.max_elevation,
                "average_elevation": snapshot.average_elevation
            }
            for snapshot in result.snapshots
        ]
    }
    
    if output_path:
        print(f"\n結果已輸出為 JSON 格式")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def save_result(result, output_path):
    """儲存結果到檔案"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "coverage_id": result.coverage_id,
        "observer": result.observer,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "statistics": {
            "duration_minutes": result.statistics.duration_minutes,
            "average_visible_count": result.statistics.average_visible_count,
            "max_visible_count": result.statistics.max_visible_count,
            "min_visible_count": result.statistics.min_visible_count,
            "coverage_percentage": result.statistics.coverage_percentage,
            "total_snapshots": result.statistics.total_snapshots
        },
        "optimal_windows": result.optimal_windows,
        "snapshots": [
            {
                "timestamp": snapshot.timestamp,
                "visible_count": snapshot.visible_count,
                "max_elevation": snapshot.max_elevation,
                "average_elevation": snapshot.average_elevation,
                "visible_satellites": [
                    {
                        "satellite_name": sat.satellite_name,
                        "azimuth": sat.azimuth,
                        "elevation": sat.elevation,
                        "distance": sat.distance,
                        "is_sunlit": sat.is_sunlit
                    }
                    for sat in snapshot.visible_satellites
                ]
            }
            for snapshot in result.snapshots
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())