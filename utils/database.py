from utils.supabase_db import SupabaseDB

# GoogleSheetDB 클래스를 SupabaseDB로 대체하는 별칭 생성
class GoogleSheetDB(SupabaseDB):
    """
    기존 GoogleSheetDB 클래스를 SupabaseDB로 대체하는 별칭 클래스
    기존 코드의 호환성을 유지하기 위해 사용됩니다.
    """
    def __init__(self):
        super().__init__()
        print("[DEBUG] GoogleSheetDB 클래스가 SupabaseDB로 대체되었습니다.") 