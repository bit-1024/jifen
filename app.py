from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps

# 安全导入 qrcode 模块
import sys
current_dir = os.getcwd()
if current_dir in sys.path:
    sys.path.remove(current_dir)

import qrcode

# 创建 Flask 应用实例
app = Flask(__name__)

# 设置密钥用于 session 和 flash 消息
app.secret_key = 'points-management-system-secret-key-2024'

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 用户数据文件
USERS_FILE = 'users.csv'

# 初始化用户数据文件
def init_users_file():
    """初始化用户数据文件"""
    if not os.path.exists(USERS_FILE):
        # 创建默认管理员账户
        default_users = pd.DataFrame({
            'username': ['admin'],
            'password_hash': [hash_password('admin123')],
            'email': ['admin@example.com'],
            'role': ['admin'],
            'created_at': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'is_active': [True]
        })
        default_users.to_csv(USERS_FILE, index=False)

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash

def login_required(f):
    """登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' not in session:
        return None

    try:
        users_df = pd.read_csv(USERS_FILE)
        user = users_df[users_df['username'] == session['user_id']]
        if not user.empty:
            return user.iloc[0].to_dict()
    except:
        pass
    return None

def create_user(username, password, email, role='user'):
    """创建新用户"""
    try:
        users_df = pd.read_csv(USERS_FILE)

        # 检查用户名是否已存在
        if not users_df[users_df['username'] == username].empty:
            return False, "用户名已存在"

        # 检查邮箱是否已存在
        if not users_df[users_df['email'] == email].empty:
            return False, "邮箱已存在"

        # 添加新用户
        new_user = pd.DataFrame({
            'username': [username],
            'password_hash': [hash_password(password)],
            'email': [email],
            'role': [role],
            'created_at': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'is_active': [True]
        })

        users_df = pd.concat([users_df, new_user], ignore_index=True)
        users_df.to_csv(USERS_FILE, index=False)

        return True, "用户创建成功"
    except Exception as e:
        return False, f"创建用户失败: {str(e)}"

# 初始化用户数据文件
init_users_file()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 配置二维码保存文件夹
QR_FOLDER = 'static/qr_codes'
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)
app.config['QR_FOLDER'] = QR_FOLDER

def generate_general_qr_code(query_url):
    """
    生成通用查询二维码
    """
    filename = "general_query_qr.png"
    file_path = os.path.join(app.config['QR_FOLDER'], filename)

    # 确保目录存在
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

    try:
        # 创建二维码实例
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # 添加数据
        qr.add_data(query_url)
        qr.make(fit=True)

        # 生成图片
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path)

        return {
            'query_url': query_url,
            'filename': filename,
            'file_path': file_path,
            'web_path': f"/static/qr_codes/{filename}"
        }

    except Exception as e:
        print(f"❌ 通用二维码生成失败: {e}")
        raise Exception(str(e))

def process_points_accumulation(new_points, daily_stats, user_info_df=None):
    """
    处理积分累计和90天过期机制
    """
    from datetime import datetime, timedelta

    # 当前日期
    current_date = datetime.now().date()
    cutoff_date = current_date - timedelta(days=90)

    # 读取当前用户的历史积分记录
    points_history_file = get_user_data_path('points_history.csv')
    if os.path.exists(points_history_file):
        history_df = pd.read_csv(points_history_file)
        history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
        history_df['UserID'] = history_df['UserID'].astype(str)
    else:
        # 创建空的历史记录
        history_df = pd.DataFrame(columns=['UserID', 'Date', 'Points'])

    # 添加新的积分记录（检查重复）
    new_records = []
    for _, row in daily_stats.iterrows():
        user_id = str(row['UserID'])
        date = row['Date']

        # 检查该用户在该日期是否已有记录
        existing_record = history_df[
            (history_df['UserID'] == user_id) &
            (history_df['Date'] == date)
        ]

        # 如果没有记录，则添加新记录
        if existing_record.empty:
            new_records.append({
                'UserID': user_id,
                'Date': date,
                'Points': 1  # 每天最多1分
            })

    if new_records:
        new_df = pd.DataFrame(new_records)
        history_df = pd.concat([history_df, new_df], ignore_index=True)
        print(f"✅ 添加了 {len(new_records)} 条新的积分记录")

    # 移除90天前的积分记录
    history_df = history_df[history_df['Date'] > cutoff_date]

    # 去重（同一用户同一天只能有一条记录）
    history_df = history_df.drop_duplicates(subset=['UserID', 'Date'], keep='last')

    # 保存更新后的历史记录
    history_df.to_csv(points_history_file, index=False)

    # 计算每个用户的总积分
    user_points = history_df.groupby('UserID')['Points'].sum().reset_index()
    user_points.columns = ['UserID', 'TotalPoints']
    user_points['UserID'] = user_points['UserID'].astype(str)

    # 添加有效期信息
    user_points['ValidDays'] = history_df.groupby('UserID').size().reset_index(name='ValidDays')['ValidDays']

    # 添加用户昵称信息
    if user_info_df is not None and 'UserName' in user_info_df.columns:
        # 获取每个用户的最新昵称
        user_names = user_info_df.groupby('UserID')['UserName'].last().reset_index()
        user_names['UserID'] = user_names['UserID'].astype(str)
        user_points = user_points.merge(user_names, on='UserID', how='left')
        user_points['UserName'] = user_points['UserName'].fillna('未知用户')
    else:
        user_points['UserName'] = '未知用户'

    # 保存当前用户的积分文件
    user_points_file = get_user_data_path('user_points.csv')
    user_points.to_csv(user_points_file, index=False)

    return user_points

def get_user_data_path(filename, user_id=None):
    """
    获取用户专属的数据文件路径
    """
    if user_id is None:
        user_id = session.get('user_id', 'default')

    # 创建用户专属目录
    user_dir = os.path.join('data', user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    return os.path.join(user_dir, filename)

def get_system_stats():
    """
    获取系统统计数据（当前用户的数据）
    """
    try:
        stats = {
            'total_users': 0,
            'total_points': 0,
            'active_users': 0
        }

        # 读取当前用户的积分数据
        user_points_file = get_user_data_path('user_points.csv')
        if os.path.exists(user_points_file):
            user_points = pd.read_csv(user_points_file)

            # 总用户数
            stats['total_users'] = len(user_points)

            # 累计积分
            stats['total_points'] = int(user_points['TotalPoints'].sum())

            # 活跃用户数（积分>0的用户）
            stats['active_users'] = len(user_points[user_points['TotalPoints'] > 0])

        return stats

    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        return {
            'total_users': 0,
            'total_points': 0,
            'active_users': 0
        }

def extract_date_from_data(df):
    """
    从数据中提取日期信息，支持多种日期格式和历史数据
    """
    from datetime import datetime, timedelta

    date_column = None

    # 优先使用开始时间
    if 'StartTime' in df.columns:
        date_column = 'StartTime'
    elif 'EndTime' in df.columns:
        date_column = 'EndTime'

    if date_column and pd.api.types.is_datetime64_any_dtype(df[date_column]):
        # 如果已经是datetime类型，直接提取日期
        df['Date'] = df[date_column].dt.date
    elif date_column:
        # 尝试解析时间字符串
        try:
            df['Date'] = pd.to_datetime(df[date_column]).dt.date
        except:
            # 如果解析失败，使用当前日期
            df['Date'] = datetime.now().date()
            print(f"⚠️ 警告: 无法解析时间列 {date_column}，使用当前日期")
    else:
        # 没有时间列，检查是否有其他可能的日期列
        possible_date_columns = [col for col in df.columns if '时间' in col or '日期' in col or 'date' in col.lower() or 'time' in col.lower()]

        if possible_date_columns:
            # 尝试使用第一个可能的日期列
            try:
                df['Date'] = pd.to_datetime(df[possible_date_columns[0]]).dt.date
                print(f"✅ 使用列 '{possible_date_columns[0]}' 作为日期")
            except:
                df['Date'] = datetime.now().date()
                print(f"⚠️ 警告: 无法解析日期列 {possible_date_columns[0]}，使用当前日期")
        else:
            # 完全没有日期信息，使用当前日期
            df['Date'] = datetime.now().date()
            print("⚠️ 警告: 未找到任何日期列，使用当前日期")

    return df

def process_historical_data(df, cutoff_days=90):
    """
    处理历史数据，确保只保留指定天数内的数据
    """
    from datetime import datetime, timedelta

    current_date = datetime.now().date()
    cutoff_date = current_date - timedelta(days=cutoff_days)

    # 过滤掉超过有效期的数据
    if 'Date' in df.columns:
        original_count = len(df)
        df = df[df['Date'] > cutoff_date]
        filtered_count = len(df)

        if original_count > filtered_count:
            expired_count = original_count - filtered_count
            print(f"📅 过滤掉 {expired_count} 条超过 {cutoff_days} 天的历史数据")
            print(f"   保留 {filtered_count} 条有效数据（{cutoff_date} 之后）")

    return df

def clean_empty_data(df):
    """
    清理空数据和无效行
    """
    print(f"📊 数据清理前: {len(df)} 行")

    # 1. 删除完全空白的行
    df = df.dropna(how='all')
    print(f"📊 删除完全空行后: {len(df)} 行")

    # 2. 清理空字符串和空格
    # 将空字符串和只包含空格的字符串替换为NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    # 3. 识别关键列
    user_id_columns = [col for col in df.columns if any(keyword in col for keyword in ['用户', 'user', 'id', 'ID', '编号'])]
    duration_columns = [col for col in df.columns if any(keyword in col for keyword in ['时长', '时间', 'duration', 'time'])]
    name_columns = [col for col in df.columns if any(keyword in col for keyword in ['昵称', 'name', '名称', '姓名'])]

    print(f"📋 识别的关键列:")
    print(f"   用户ID列: {user_id_columns}")
    print(f"   时长列: {duration_columns}")
    print(f"   用户名列: {name_columns}")

    # 4. 删除用户ID为空的行（用户ID是必需的）
    if user_id_columns:
        for col in user_id_columns[:1]:  # 只检查第一个用户ID列
            before_count = len(df)
            df = df.dropna(subset=[col])
            after_count = len(df)
            if before_count != after_count:
                print(f"📊 删除{col}为空的行: {before_count} → {after_count} 行")

    # 5. 删除时长为空的行（时长是必需的）
    if duration_columns:
        for col in duration_columns[:1]:  # 只检查第一个时长列
            before_count = len(df)
            df = df.dropna(subset=[col])
            after_count = len(df)
            if before_count != after_count:
                print(f"📊 删除{col}为空的行: {before_count} → {after_count} 行")

    # 6. 删除所有重要列都为空的行
    important_columns = user_id_columns + duration_columns + name_columns
    if important_columns:
        before_count = len(df)
        df = df.dropna(subset=important_columns, how='all')
        after_count = len(df)
        if before_count != after_count:
            print(f"📊 删除重要列全空的行: {before_count} → {after_count} 行")

    # 7. 删除重复行
    before_count = len(df)
    df = df.drop_duplicates()
    after_count = len(df)
    if before_count != after_count:
        print(f"📊 删除重复行: {before_count} → {after_count} 行")

    # 8. 再次删除可能产生的空行
    df = df.dropna(how='all')

    # 9. 重置索引
    df = df.reset_index(drop=True)

    print(f"📊 数据清理完成: {len(df)} 行有效数据")

    # 显示清理后的数据概览
    if len(df) > 0:
        print(f"📋 清理后数据概览:")
        print(f"   列数: {len(df.columns)}")
        print(f"   列名: {list(df.columns)}")
        if len(df) <= 10:
            print(f"   所有数据行:")
            for i, (_, row) in enumerate(df.iterrows()):
                row_preview = " | ".join([f"{col}: {str(row[col])[:20]}" for col in df.columns[:3]])
                print(f"      第{i+1}行: {row_preview}")
        else:
            print(f"   前3行数据:")
            for i, (_, row) in enumerate(df.head(3).iterrows()):
                row_preview = " | ".join([f"{col}: {str(row[col])[:20]}" for col in df.columns[:3]])
                print(f"      第{i+1}行: {row_preview}")

    return df

def filter_and_paginate_user_points(user_points, page, per_page, search_user_id, search_user_name, min_points, max_points, sort_by, sort_order):
    """
    对用户积分数据进行筛选和分页处理
    """
    # 转换为DataFrame以便处理
    df = user_points.copy()

    # 确保有UserName列
    if 'UserName' not in df.columns:
        df['UserName'] = '未知用户'

    # 应用筛选条件
    if search_user_id:
        df = df[df['UserID'].astype(str).str.contains(search_user_id, case=False, na=False)]

    if search_user_name:
        df = df[df['UserName'].str.contains(search_user_name, case=False, na=False)]

    if min_points is not None:
        df = df[df['TotalPoints'] >= min_points]

    if max_points is not None:
        df = df[df['TotalPoints'] <= max_points]

    # 排序
    ascending = sort_order == 'asc'
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=ascending)

    # 计算分页
    total_records = len(df)
    total_pages = (total_records + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = df.iloc[start_idx:end_idx]

    return {
        'data': paginated_data,
        'total_records': total_records,
        'total_pages': total_pages
    }

def detect_column_mapping(columns):
    """
    智能识别表格列名，支持多种表头格式
    返回列名映射字典
    """
    column_list = [col.strip() for col in columns]
    mapping = {}

    # 用户ID相关的可能列名
    user_id_patterns = [
        '用户id', '用户ID', 'UserID', 'userid', 'user_id',
        '主播ID', '主播id', '演员ID', '演员id'
    ]

    # 用户昵称相关的可能列名
    user_name_patterns = [
        '演员人大名', '演员人名字', '用户名称', '用户配称', '用户昵称', '昵称', '姓名',
        '主播', '主播名', '演员', '用户', '用户名', 'username', 'nickname'
    ]

    # 开始时间相关的可能列名
    start_time_patterns = [
        '首次观看直播时间', '开始时间', 'StartTime', 'start_time', 'starttime',
        '直播开始时间', '开播时间', '首次进入时间', '进入时间', '开始'
    ]

    # 结束时间相关的可能列名
    end_time_patterns = [
        '最后观看直播时间', '最近观看直播时间', '最后离开直播时间', '结束时间', 'EndTime', 'end_time', 'endtime',
        '直播结束时间', '离开时间', '结束'
    ]

    # 观看时长相关的可能列名
    duration_patterns = [
        '直播观看时长', '观看时长', '时长', 'Duration', 'duration',
        '观看时间', '直播时间', '在线时长', '停留时长'
    ]

    def find_best_match(column_list, patterns, mapping_key):
        """查找最佳匹配的列"""
        # 首先尝试精确匹配
        for col in column_list:
            col_lower = col.lower()
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if col_lower == pattern_lower:
                    return col

        # 然后尝试包含匹配
        for col in column_list:
            col_lower = col.lower()
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in col_lower:
                    return col

        return None

    # 查找各种列
    user_id_col = find_best_match(column_list, user_id_patterns, 'UserID')
    if user_id_col:
        mapping[user_id_col] = 'UserID'

    user_name_col = find_best_match(column_list, user_name_patterns, 'UserName')
    if user_name_col:
        mapping[user_name_col] = 'UserName'

    start_time_col = find_best_match(column_list, start_time_patterns, 'StartTime')
    if start_time_col:
        mapping[start_time_col] = 'StartTime'

    end_time_col = find_best_match(column_list, end_time_patterns, 'EndTime')
    if end_time_col:
        mapping[end_time_col] = 'EndTime'

    duration_col = find_best_match(column_list, duration_patterns, 'Duration')
    if duration_col:
        mapping[duration_col] = 'Duration'

    # 检查是否找到了必要的列
    found_mappings = set(mapping.values())

    # 必须有用户ID
    if 'UserID' not in found_mappings:
        return None

    # 必须有时长信息：要么有Duration列，要么有StartTime和EndTime列
    has_duration = 'Duration' in found_mappings
    has_time_range = 'StartTime' in found_mappings and 'EndTime' in found_mappings

    if has_duration or has_time_range:
        return mapping
    else:
        return None

def parse_duration_column(duration_series):
    """
    解析时长列，支持多种格式
    例如：'0小时43分53秒', '1:30:45', '90分钟' 等
    """
    import re

    def parse_single_duration(duration_str):
        if pd.isna(duration_str):
            return None

        duration_str = str(duration_str).strip()

        # 格式1: "0小时43分53秒"
        chinese_pattern = r'(\d+)小时(\d+)分(\d+)秒'
        match = re.search(chinese_pattern, duration_str)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            return hours * 60 + minutes + seconds / 60

        # 格式2: "43分53秒"
        chinese_pattern2 = r'(\d+)分(\d+)秒'
        match = re.search(chinese_pattern2, duration_str)
        if match:
            minutes, seconds = map(int, match.groups())
            return minutes + seconds / 60

        # 格式3: "1:30:45" (时:分:秒)
        time_pattern = r'(\d+):(\d+):(\d+)'
        match = re.search(time_pattern, duration_str)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            return hours * 60 + minutes + seconds / 60

        # 格式4: "90:30" (分:秒)
        time_pattern2 = r'(\d+):(\d+)'
        match = re.search(time_pattern2, duration_str)
        if match:
            minutes, seconds = map(int, match.groups())
            return minutes + seconds / 60

        # 格式5: "90分钟" 或 "90分"
        minute_pattern = r'(\d+)分'
        match = re.search(minute_pattern, duration_str)
        if match:
            minutes = int(match.group(1))
            return minutes

        # 格式6: 纯数字（假设为分钟）
        if duration_str.isdigit():
            return float(duration_str)

        # 无法解析
        return None

    return duration_series.apply(parse_single_duration)

def parse_datetime_column(datetime_series):
    """
    解析时间列，支持多种时间格式
    """
    def parse_single_datetime(datetime_str):
        if pd.isna(datetime_str):
            return None

        datetime_str = str(datetime_str).strip()

        # 常见的时间格式列表
        time_formats = [
            '%Y-%m-%d %H:%M:%S',      # 2023-03-10 17:05:35
            '%Y/%m/%d %H:%M:%S',      # 2023/03/10 17:05:35
            '%Y-%m-%d %H:%M',         # 2023-03-10 17:05
            '%Y/%m/%d %H:%M',         # 2023/03/10 17:05
            '%Y-%m-%d',               # 2023-03-10
            '%Y/%m/%d',               # 2023/03/10
            '%m/%d/%Y %H:%M:%S',      # 03/10/2023 17:05:35
            '%m-%d-%Y %H:%M:%S',      # 03-10-2023 17:05:35
            '%d/%m/%Y %H:%M:%S',      # 10/03/2023 17:05:35
            '%d-%m-%Y %H:%M:%S',      # 10-03-2023 17:05:35
        ]

        # 尝试各种格式
        for fmt in time_formats:
            try:
                return pd.to_datetime(datetime_str, format=fmt)
            except:
                continue

        # 如果所有格式都失败，尝试pandas的智能解析
        try:
            return pd.to_datetime(datetime_str, errors='coerce')
        except:
            return None

    return datetime_series.apply(parse_single_datetime)

def process_uploaded_file(file_path):
    """
    处理上传的文件，支持 CSV、Excel 等格式，计算积分
    """
    try:
        # 根据文件扩展名选择读取方法
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension == '.json':
            df = pd.read_json(file_path)
        elif file_extension == '.tsv':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8-sig')
        else:
            return {
                'success': False,
                'error': f'不支持的文件格式: {file_extension}。支持的格式: .csv, .xlsx, .xls, .json, .tsv'
            }

        print(f"📊 原始文件读取: {len(df)} 行")

        # 清理空数据和无效行
        df = clean_empty_data(df)

        if df.empty:
            return {
                'success': False,
                'error': '文件中没有有效数据，请检查文件内容'
            }

        # 智能识别列名，支持多种表头格式
        column_mapping = detect_column_mapping(df.columns)
        if not column_mapping:
            return {
                'success': False,
                'error': f'无法识别表格结构。请确保包含用户ID、开始时间、结束时间相关的列。\n当前列名: {list(df.columns)}'
            }

        # 重命名列为标准格式
        df = df.rename(columns=column_mapping)

        # 处理数据
        try:
            df['UserID'] = df['UserID'].astype(str)

            # 处理时长数据 - 支持两种方式
            if 'Duration' in df.columns:
                # 方式1：直接使用观看时长列
                df['Duration'] = parse_duration_column(df['Duration'])
                # 移除时长解析失败的行
                df = df.dropna(subset=['Duration'])
            else:
                # 方式2：使用开始和结束时间计算时长
                df['StartTime'] = parse_datetime_column(df['StartTime'])
                df['EndTime'] = parse_datetime_column(df['EndTime'])

                # 移除时间解析失败的行
                df = df.dropna(subset=['StartTime', 'EndTime'])

                if df.empty:
                    return {
                        'success': False,
                        'error': '时间数据格式错误，无法解析开始时间和结束时间'
                    }

                df['Duration'] = (df['EndTime'] - df['StartTime']).dt.total_seconds() / 60

            if df.empty:
                return {
                    'success': False,
                    'error': '无法解析时长数据，请检查数据格式'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'数据处理错误: {str(e)}'
            }

        # 筛选大于等于40分钟的记录
        filtered_df = df[df['Duration'] >= 40].copy()

        if filtered_df.empty:
            return {
                'success': False,
                'error': '没有找到持续时长大于等于40分钟的直播记录'
            }

        # 提取日期信息（支持历史数据）
        filtered_df = extract_date_from_data(filtered_df)

        # 处理历史数据（过滤超过90天的数据）
        filtered_df = process_historical_data(filtered_df, cutoff_days=90)

        if filtered_df.empty:
            return {
                'success': False,
                'error': '所有数据都超过了90天有效期，无法获得积分'
            }

        daily_stats = filtered_df.groupby(['UserID', 'Date']).size().reset_index(name='Count')
        new_points = daily_stats.groupby('UserID').size().reset_index(name='NewPoints')
        new_points['UserID'] = new_points['UserID'].astype(str)

        # 处理积分累计和过期
        user_points = process_points_accumulation(new_points, daily_stats, filtered_df)

        return {
            'success': True,
            'user_points': user_points,
            'total_users': len(user_points)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 定义根路由
# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        try:
            users_df = pd.read_csv(USERS_FILE)
            user = users_df[users_df['username'] == username]

            if user.empty:
                flash('用户名不存在', 'error')
                return render_template('login.html')

            user_data = user.iloc[0]

            if not user_data['is_active']:
                flash('账户已被禁用', 'error')
                return render_template('login.html')

            if verify_password(password, user_data['password_hash']):
                session['user_id'] = username
                session['user_role'] = user_data['role']
                session['just_logged_in'] = True  # 标记刚刚登录
                return redirect(url_for('admin_upload'))
            else:
                flash('密码错误', 'error')
                return render_template('login.html')

        except Exception as e:
            flash(f'登录失败: {str(e)}', 'error')
            return render_template('login.html')

    return render_template('login.html')

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证输入
        if not all([username, email, password, confirm_password]):
            flash('请填写所有必填字段', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('密码至少需要6个字符', 'error')
            return render_template('register.html')

        # 创建用户
        success, message = create_user(username, password, email, 'admin')

        if success:
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('register.html')

    return render_template('register.html')

# 登出路由
@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('已成功登出', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    """
    主页路由
    显示系统首页和统计信息
    """
    try:
        # 获取系统统计数据
        stats = get_system_stats()
        return render_template('index.html', stats=stats)
    except Exception as e:
        # 如果获取统计数据失败，仍然显示首页但不显示统计
        return render_template('index.html', stats=None)

# 管理员上传页面路由
@app.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def admin_upload():
    """
    管理员上传页面
    GET: 显示上传表单
    POST: 处理文件上传
    """
    if request.method == 'GET':
        # 检查是否刚刚登录
        just_logged_in = session.pop('just_logged_in', False)
        current_user = get_current_user()

        # 渲染合并的上传页面模板
        return render_template('admin_upload_combined.html',
                             show_results=False,
                             upload_result=None,
                             just_logged_in=just_logged_in,
                             current_user=current_user)

    elif request.method == 'POST':
        # 处理文件上传
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)

        file = request.files['file']

        # 检查是否选择了文件
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)

        # 检查文件类型（支持多种格式）
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json', '.tsv']
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file and file_extension in allowed_extensions:
            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # 处理上传的文件
            result = process_uploaded_file(file_path)

            if result['success']:
                user_points = result['user_points']
                base_url = request.host_url.rstrip('/')

                # 生成通用查询二维码
                general_qr_info = None
                try:
                    query_url = f"{base_url}/query"  # 通用查询页面
                    general_qr_info = generate_general_qr_code(query_url)
                except Exception as e:
                    flash(f'通用二维码生成失败: {str(e)}', 'error')

                # 不使用flash消息，改为在页面内显示成功信息

                # 获取分页和筛选参数
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 10, type=int)
                search_user_id = request.args.get('search_user_id', '').strip()
                search_user_name = request.args.get('search_user_name', '').strip()
                min_points = request.args.get('min_points', type=int)
                max_points = request.args.get('max_points', type=int)
                sort_by = request.args.get('sort_by', 'TotalPoints')
                sort_order = request.args.get('sort_order', 'desc')

                # 处理用户积分数据的分页和筛选
                filtered_user_points = filter_and_paginate_user_points(
                    user_points, page, per_page, search_user_id, search_user_name,
                    min_points, max_points, sort_by, sort_order
                )

                return render_template('admin_upload_combined.html',
                                     show_results=True,
                                     upload_result={
                                         'filename': filename,
                                         'total_users': result['total_users'],
                                         'user_points': filtered_user_points['data'],
                                         'total_records': filtered_user_points['total_records'],
                                         'total_pages': filtered_user_points['total_pages'],
                                         'current_page': page,
                                         'per_page': per_page,
                                         'general_qr': general_qr_info,
                                         'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                         'search_params': {
                                             'search_user_id': search_user_id,
                                             'search_user_name': search_user_name,
                                             'min_points': min_points,
                                             'max_points': max_points,
                                             'sort_by': sort_by,
                                             'sort_order': sort_order
                                         }
                                     })
            else:
                flash(f'处理失败: {result["error"]}', 'error')
                return redirect(request.url)
        else:
            flash(f'不支持的文件格式。支持的格式: {", ".join(allowed_extensions)}', 'error')
            return redirect(request.url)

# 积分管理页面
@app.route('/admin/points')
@login_required
def admin_points():
    """
    积分管理页面，查看积分历史和过期情况，支持分页和筛选
    """
    try:
        from datetime import datetime, timedelta

        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_user_id = request.args.get('search_user_id', '').strip()
        search_user_name = request.args.get('search_user_name', '').strip()
        min_points = request.args.get('min_points', type=int)
        max_points = request.args.get('max_points', type=int)
        sort_by = request.args.get('sort_by', 'TotalPoints')
        sort_order = request.args.get('sort_order', 'desc')

        # 读取当前用户的积分数据
        user_points_file = get_user_data_path('user_points.csv')
        if os.path.exists(user_points_file):
            user_stats = pd.read_csv(user_points_file)
            user_stats['UserID'] = user_stats['UserID'].astype(str)

            # 确保有UserName列
            if 'UserName' not in user_stats.columns:
                user_stats['UserName'] = '未知用户'

            # 应用筛选条件
            if search_user_id:
                user_stats = user_stats[user_stats['UserID'].str.contains(search_user_id, case=False, na=False)]

            if search_user_name:
                user_stats = user_stats[user_stats['UserName'].str.contains(search_user_name, case=False, na=False)]

            if min_points is not None:
                user_stats = user_stats[user_stats['TotalPoints'] >= min_points]

            if max_points is not None:
                user_stats = user_stats[user_stats['TotalPoints'] <= max_points]

            # 排序
            ascending = sort_order == 'asc'
            if sort_by in user_stats.columns:
                user_stats = user_stats.sort_values(sort_by, ascending=ascending)

            # 计算分页
            total_records = len(user_stats)
            total_pages = (total_records + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_stats = user_stats.iloc[start_idx:end_idx]

            # 读取历史记录数量
            points_history_file = 'points_history.csv'
            history_count = 0
            if os.path.exists(points_history_file):
                history_df = pd.read_csv(points_history_file)
                history_count = len(history_df)

            # 获取当前用户信息
            current_user = get_current_user()

            return render_template('admin_points.html',
                                 user_stats=paginated_stats,
                                 total_records=total_records,
                                 total_pages=total_pages,
                                 current_page=page,
                                 per_page=per_page,
                                 history_count=history_count,
                                 current_date=datetime.now().date(),
                                 current_user=current_user,
                                 search_params={
                                     'search_user_id': search_user_id,
                                     'search_user_name': search_user_name,
                                     'min_points': min_points,
                                     'max_points': max_points,
                                     'sort_by': sort_by,
                                     'sort_order': sort_order
                                 })
        else:
            # 获取当前用户信息
            current_user = get_current_user()

            return render_template('admin_points.html',
                                 user_stats=pd.DataFrame(),
                                 total_records=0,
                                 total_pages=0,
                                 current_page=1,
                                 per_page=per_page,
                                 history_count=0,
                                 current_date=datetime.now().date(),
                                 current_user=current_user,
                                 search_params={})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"积分管理页面错误: {error_details}")
        flash(f'读取积分数据失败: {str(e)}', 'error')
        return redirect(url_for('admin_upload'))

# 通用查询页面
@app.route('/query')
def query_page():
    """
    通用查询页面，用户可以输入用户名查询积分
    """
    return render_template('query_page.html')

# 用户查询接口
@app.route('/query/<user_name>')
def query_user(user_name):
    """
    用户查询接口 - 根据用户名查询
    """
    try:
        # 检查是否有登录用户的数据
        user_points_file = None
        if 'user_id' in session:
            user_points_file = get_user_data_path('user_points.csv')

        # 如果没有登录用户，尝试查找所有用户的数据
        if not user_points_file or not os.path.exists(user_points_file):
            # 查找data目录下所有用户的数据
            data_dir = 'data'
            found_data = False
            combined_df = pd.DataFrame()

            if os.path.exists(data_dir):
                for user_dir in os.listdir(data_dir):
                    user_data_file = os.path.join(data_dir, user_dir, 'user_points.csv')
                    if os.path.exists(user_data_file):
                        try:
                            temp_df = pd.read_csv(user_data_file)
                            combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
                            found_data = True
                        except:
                            continue

            if not found_data:
                return render_template('query_result.html',
                                     user_name=user_name,
                                     error_message="积分数据文件不存在，请先上传数据文件")

            df = combined_df
        else:
            df = pd.read_csv(user_points_file)
        df['UserID'] = df['UserID'].astype(str)

        # 确保有UserName列
        if 'UserName' not in df.columns:
            return render_template('query_result.html',
                                 user_name=user_name,
                                 error_message="系统暂不支持用户名查询，请联系管理员")

        # 查找用户（支持模糊匹配）
        user_records = df[df['UserName'].str.contains(str(user_name), case=False, na=False)]

        if not user_records.empty:
            # 如果找到多个用户，返回所有匹配的用户
            if len(user_records) > 1:
                users_list = []
                for _, user_info in user_records.iterrows():
                    users_list.append({
                        'UserID': user_info['UserID'],
                        'UserName': user_info['UserName'],
                        'TotalPoints': int(user_info['TotalPoints']),
                        'ValidDays': int(user_info['ValidDays']) if 'ValidDays' in user_info else 0
                    })

                return render_template('query_result.html',
                                     user_name=user_name,
                                     users_list=users_list,
                                     multiple=True,
                                     found=True,
                                     message=f"找到{len(user_records)}个匹配的用户")

            # 只找到一个用户
            user_info = user_records.iloc[0]
            return render_template('query_result.html',
                                 user_name=user_name,
                                 user_id=user_info['UserID'],
                                 user_display_name=user_info['UserName'],
                                 total_points=int(user_info['TotalPoints']),
                                 valid_days=int(user_info['ValidDays']) if 'ValidDays' in user_info else 0,
                                 multiple=False,
                                 found=True)
        else:
            return render_template('query_result.html',
                                 user_name=user_name,
                                 error_message=f"未找到用户名包含'{user_name}'的积分记录",
                                 found=False)

    except Exception as e:
        return render_template('query_result.html',
                             user_name=user_name,
                             error_message=f"查询错误：{str(e)}")

# 运行应用
if __name__ == '__main__':
    # 开启调试模式，方便开发
    app.run(debug=True, host='0.0.0.0', port=5000)
