import json
import requests
import argparse
import time
import os
from pathlib import Path

# URL và Headers
SWIFTPOD_API_BASE = "http://localhost:9000/app/products"

SWIFTPOD_HEADERS = {
    "accept": "*/*",
    "accept-language": "en,en-US;q=0.9,vi;q=0.8",
    "origin": "http://localhost:9000/app",
    "referer": "http://localhost:9000/app/",
    "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
}

SLUG_PRODUCT = [
    "gildan-5000",
    "comfort-color-1717",
    "bella-3001", 
    "gildan-18000",
    "gildan-18500",
    "gildan-64000",
    "gildan-5000l",
    "gildan-5000b",
    "nextlevel-6210",
    "next-level-3600",
]


def fetch_swiftpod_collection(product_type, limit=50):
    """Lấy danh sách sản phẩm từ SwiftPod API theo trang"""
    page = 1
    all_products = []
    
    while True:
        print(f"🔍 Đang lấy trang {page} cho loại sản phẩm: {product_type}")
        url = f"{SWIFTPOD_API_BASE}/search?page={page}&limit={limit}&product_type={product_type}"
        
        try:
            response = requests.get(url, headers=SWIFTPOD_HEADERS)
            response.raise_for_status()
            collection_data = response.json()
            
            # Lấy danh sách sản phẩm từ phản hồi
            products = collection_data.get("products", {}).get("data", [])
            
            if not products:
                print(f"✅ Đã lấy xong tất cả sản phẩm ({len(all_products)} sản phẩm)")
                break
                
            all_products.extend(products)
            print(f"✅ Đã lấy được {len(products)} sản phẩm từ trang {page}")
            
            # Kiểm tra xem có trang tiếp theo không
            next_page = collection_data.get("products", {}).get("next_page_url")
            if not next_page:
                print(f"✅ Đã lấy xong tất cả sản phẩm ({len(all_products)} sản phẩm)")
                break
                
            page += 1
            # Tạm dừng một chút để tránh gửi quá nhiều request
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi lấy dữ liệu từ SwiftPod: {e}")
            break
    
    return all_products

def fetch_product_detail(slug):
    """Lấy thông tin chi tiết của một sản phẩm dựa trên slug"""
    print(f"🔍 Đang lấy thông tin chi tiết cho sản phẩm: {slug}")
    url = f"{SWIFTPOD_API_BASE}/products/{slug}?client=true"
    
    try:
        response = requests.get(url, headers=SWIFTPOD_HEADERS)
        response.raise_for_status()
        product_data = response.json()
        print(f"✅ Đã lấy được thông tin chi tiết cho sản phẩm: {product_data.get('name', 'Unknown')}")
        return product_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi lấy thông tin chi tiết sản phẩm {slug}: {e}")
        return None

def split_products_into_chunks(products, chunk_size=20):
    """Chia danh sách sản phẩm thành các phần nhỏ hơn"""
    for i in range(0, len(products), chunk_size):
        yield products[i:i + chunk_size]

def main():
    parser = argparse.ArgumentParser(description="Lấy và chia nhỏ sản phẩm từ SwiftPod API thành các file JSON")
    parser.add_argument("--product-type", help="Loại sản phẩm cần lấy (ví dụ: mugs, tshirts)")
    parser.add_argument("--limit", type=int, default=50, help="Số lượng sản phẩm mỗi trang")
    parser.add_argument("--chunk-size", type=int, default=20, help="Số lượng sản phẩm trong mỗi file JSON")
    parser.add_argument("--output-dir", default="products_data", help="Thư mục đầu ra chứa các file JSON")
    parser.add_argument("--slugs", nargs="+", help="Danh sách các slug cần lấy dữ liệu (ví dụ: gildan-64000 comfort-color-1717)")
    parser.add_argument("--slugdetail", action="store_true", help="Lấy dữ liệu chi tiết của tất cả các slug trong SLUG_PRODUCT")
    args = parser.parse_args()
    
    # Tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    detailed_products = []
    
    if args.slugdetail:
        # Lấy dữ liệu chi tiết của tất cả các slug trong SLUG_PRODUCT
        print(f"🚀 Bắt đầu lấy dữ liệu chi tiết cho {len(SLUG_PRODUCT)} slug từ SLUG_PRODUCT")
        
        for index, slug in enumerate(SLUG_PRODUCT):
            print(f"\n[{index+1}/{len(SLUG_PRODUCT)}] Đang xử lý slug: {slug}")
            detailed_product = fetch_product_detail(slug)
            
            if detailed_product:
                detailed_products.append(detailed_product)
            
            # Tạm dừng giữa các sản phẩm để tránh gửi quá nhiều request
            if index < len(SLUG_PRODUCT) - 1:
                print("⏱️ Đang tạm dừng 1 giây trước khi xử lý sản phẩm tiếp theo...")
                time.sleep(1)
        
        # Lưu kết quả vào file JSON
        output_file = output_dir / "slugdetailco.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_products, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Đã hoàn thành! Đã lưu dữ liệu chi tiết của {len(detailed_products)} sản phẩm vào file: {output_file}")
        return
    
    if not args.product_type:
        print("❌ Vui lòng chỉ định loại sản phẩm (--product-type) hoặc sử dụng --slugdetail")
        return
    
    print(f"🚀 Bắt đầu quá trình lấy và chia nhỏ sản phẩm loại: {args.product_type}")
    
    if args.slugs:
        # Nếu có chỉ định slugs, chỉ lấy dữ liệu của các slug đó
        print(f"📋 Đang lấy dữ liệu cho {len(args.slugs)} slug được chỉ định")
        for index, slug in enumerate(args.slugs):
            print(f"\n[{index+1}/{len(args.slugs)}] Đang xử lý slug: {slug}")
            detailed_product = fetch_product_detail(slug)
            
            if detailed_product:
                detailed_products.append(detailed_product)
            
            # Tạm dừng giữa các sản phẩm để tránh gửi quá nhiều request
            if index < len(args.slugs) - 1:
                print("⏱️ Đang tạm dừng 1 giây trước khi xử lý sản phẩm tiếp theo...")
                time.sleep(1)
    else:
        # Nếu không có chỉ định slugs, lấy tất cả sản phẩm như cũ
        # Bước 1: Lấy danh sách sản phẩm
        products = fetch_swiftpod_collection(args.product_type, args.limit)
        
        if not products:
            print("❌ Không tìm thấy sản phẩm nào, kết thúc chương trình")
            return
        
        # Lưu toàn bộ sản phẩm vào một file JSON
        full_products_file = output_dir / f"{args.product_type}_all_products.json"
        with open(full_products_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu tất cả {len(products)} sản phẩm vào file: {full_products_file}")
        
        # Bước 2: Lấy thông tin chi tiết cho mỗi sản phẩm
        for index, product in enumerate(products):
            print(f"\n[{index+1}/{len(products)}] Đang xử lý: {product['name']}")
            detailed_product = fetch_product_detail(product['slug'])
            
            if detailed_product:
                detailed_products.append(detailed_product)
            
            # Tạm dừng giữa các sản phẩm để tránh gửi quá nhiều request
            if index < len(products) - 1:
                print("⏱️ Đang tạm dừng 1 giây trước khi xử lý sản phẩm tiếp theo...")
                time.sleep(1)
    
    if not detailed_products:
        print("❌ Không lấy được dữ liệu chi tiết của sản phẩm nào, kết thúc chương trình")
        return
    
    # Lưu toàn bộ sản phẩm chi tiết vào một file JSON
    full_detailed_file = output_dir / f"{args.product_type}_all_detailed.json"
    with open(full_detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_products, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu tất cả {len(detailed_products)} sản phẩm chi tiết vào file: {full_detailed_file}")
    
    # Bước 3: Chia nhỏ sản phẩm thành các file JSON
    chunks = list(split_products_into_chunks(detailed_products, args.chunk_size))
    
    for i, chunk in enumerate(chunks):
        chunk_file = output_dir / f"{args.product_type}_chunk_{i+1}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu {len(chunk)} sản phẩm vào file chunk: {chunk_file}")
    
    print(f"\n✅ Đã hoàn thành! Đã chia {len(detailed_products)} sản phẩm thành {len(chunks)} file chunk")
    print(f"📁 Các file được lưu trong thư mục: {output_dir}")

if __name__ == "__main__":
    main() 