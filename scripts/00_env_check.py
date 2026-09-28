import pandas as pd

# 환경 확인용 가상 예시
data = {
    "테마명": ["가짜 테마 하나", "가짜 테마 둘", "가짜 테마 셋"],
    "가격": [25000, 30000, 35000]
}

df = pd.DataFrame(data)

print("환경 확인용 가상 예시")
print(df)
print(df.shape)
import requests
import bs4
import matplotlib

print("pandas:", pd.__version__)
print("requests:", requests.__version__)
print("beautifulsoup4:", bs4.__version__)
print("matplotlib:", matplotlib.__version__)