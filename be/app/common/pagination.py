# Tầng dùng chung: khai báo phân trang cho các API quản trị mới.
from dataclasses import dataclass


@dataclass(frozen=True)
class Pagination:
    limit: int = 50
    offset: int = 0
