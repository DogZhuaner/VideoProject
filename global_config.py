from pathlib import Path

from markdown_it.rules_core.normalize import NULL_RE


class Global_Config:
    ProjectRoot = Path(__file__).resolve().parent
    #image
    image_root = str(ProjectRoot / 'image')
    selectSwitchArea = str(ProjectRoot/'image'/'fullscreen.jpg')
    live_capture_path = str(ProjectRoot/'image'/'live_capture.png')
    standard_path = str(ProjectRoot/'image'/'standard.jpg')
    history_capture_dir = str(ProjectRoot/ 'image' / 'Hand_capture')
    #data
    label_6area_path = ProjectRoot/'data'/'label'/'4_area'
    label_30area_path =ProjectRoot/'data'/'label'/'30_area'
    final_result_path = ProjectRoot/'data'/'result'
    predict_txt_path =ProjectRoot/'data'/'result'/'data'
    split_path = ProjectRoot/'image'/'split'
    region_json_path = str(ProjectRoot/'data'/'regions_rules.json')
    rule_path = ProjectRoot/'data'/'result'  # 修正：指向包含rule.csv的目录
    union_find_json_path = str(ProjectRoot/'data'/'result'/'union_find.json')
    rule_json_path = str(ProjectRoot/'data'/'rules'/'rule1.json')
    # 具体的文件路径
    result_csv_path = str(ProjectRoot/'data'/'result'/'new')  # 检测结果CSV文件
    old_result_csv_path = str(ProjectRoot/'data'/'result'/'old')
    rule_csv_path = str(ProjectRoot/'data'/'result'/'rule.csv')      # 规则CSV文件
    
    #weights
    Hand_and_switch = ProjectRoot/'weights'/'hand_and_switch.pt'
    contact = ProjectRoot/'weights'/'contact.pt'

    # rule server
    rule_server_ip = '127.0.0.1'  # 默认教师端IP
    rule_server_port = 8000       # 默认端口号
    student_json = ProjectRoot/'data'/'student.json'

    switch_status = True
    error_wiring_count = 0

    # 全局分数管理
    flag=0        #判断标志
    total_score = 0   # 总分
    current_session_score = 0     # 当前会话得分
    wired_status = ""
    current_A = ""     #当前触点A
    current_B = ""     #当前触点B
    wiring_results = []           # 接线结果历史
    score_history = []            # 分数历史记录
    is_first_score = False

class Login_Session:
    user_id = ''
    username = ''
    account_name = ''
    sno = ''

# 分数管理函数
def reset_global_score():
    """重置全局分数 - 每次启动程序时调用"""
    Global_Config.total_score = 0
    Global_Config.current_session_score = 0
    Global_Config.wiring_results = []
    Global_Config.score_history = []
    print("全局分数已重置为0")

def add_global_score(score):
    """添加分数到全局总分"""
    Global_Config.total_score += score
    Global_Config.current_session_score += score
    print(f"全局分数更新: +{score}分, 当前总分: {Global_Config.total_score}分")
    return Global_Config.total_score

def get_global_score():
    """获取全局总分"""
    return Global_Config.total_score

def get_current_session_score():
    """获取当前会话得分"""
    return Global_Config.current_session_score

def add_wiring_result(end1, end2, score):
    """添加接线结果到全局记录"""
    import time
    result = {
        'end1': end1,
        'end2': end2,
        'score': score,
        'timestamp': time.time()
    }
    Global_Config.wiring_results.append(result)
    return result

def get_wiring_results():
    """获取所有接线结果"""
    return Global_Config.wiring_results.copy()

def save_session_to_history():
    """保存当前会话到历史记录"""
    import time
    if Global_Config.current_session_score > 0:
        session_record = {
            'score': Global_Config.current_session_score,
            'wiring_results': Global_Config.wiring_results.copy(),
            'timestamp': time.time()
        }
        Global_Config.score_history.append(session_record)
        print(f"会话已保存到历史记录: {Global_Config.current_session_score}分")
    return Global_Config.score_history

def reset_session_score():
    """重置当前会话分数"""
    old_session_score = Global_Config.current_session_score
    Global_Config.current_session_score = 0
    Global_Config.wiring_results = []
    print(f"会话分数已重置: {old_session_score}分 -> 0分")
    return 0

# 程序启动时自动重置分数
reset_global_score()

if __name__ == "__main__":
    print(Global_Config.weight_path)
