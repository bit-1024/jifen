from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps
from config_manager import config_manager
import json

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
    处理积分累计和过期机制（使用配置参数）
    """
    from datetime import datetime, timedelta

    # 从配置中获取有效期天数
    validity_days = config_manager.get('points_system.validity_days', 90)
    points_per_day = config_manager.get('points_system.points_per_day', 1)

    # 当前日期
    current_date = datetime.now().date()
    cutoff_date = current_date - timedelta(days=validity_days)

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
                'Points': points_per_day  # 使用配置的每日积分
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

    # 处理用户昵称信息 - 修复bug：保留已有用户的昵称
    user_points_file = get_user_data_path('user_points.csv')
    existing_user_names = {}

    # 先读取现有的用户积分文件，保留已有的用户昵称
    if os.path.exists(user_points_file):
        try:
            existing_df = pd.read_csv(user_points_file)
            if 'UserName' in existing_df.columns:
                existing_df['UserID'] = existing_df['UserID'].astype(str)
                # 创建现有用户昵称的字典
                for _, row in existing_df.iterrows():
                    if pd.notna(row['UserName']) and row['UserName'] != '未知用户':
                        existing_user_names[str(row['UserID'])] = row['UserName']
                print(f"📋 保留了 {len(existing_user_names)} 个已有用户的昵称信息")
        except Exception as e:
            print(f"⚠️ 读取现有用户昵称失败: {str(e)}")

    # 初始化用户昵称列
    user_points['UserName'] = '未知用户'

    # 先使用现有的用户昵称
    for user_id in user_points['UserID']:
        if user_id in existing_user_names:
            user_points.loc[user_points['UserID'] == user_id, 'UserName'] = existing_user_names[user_id]

    # 然后用新导入的数据更新用户昵称（如果有的话）
    if user_info_df is not None and 'UserName' in user_info_df.columns:
        # 获取每个用户的最新昵称
        user_names = user_info_df.groupby('UserID')['UserName'].last().reset_index()
        user_names['UserID'] = user_names['UserID'].astype(str)

        # 更新用户昵称（只更新新导入文件中存在的用户）
        for _, row in user_names.iterrows():
            user_id = str(row['UserID'])
            user_name = row['UserName']
            if pd.notna(user_name) and user_name.strip():  # 确保昵称不为空
                user_points.loc[user_points['UserID'] == user_id, 'UserName'] = user_name.strip()

        print(f"📋 更新了 {len(user_names)} 个用户的昵称信息")

    # 保存当前用户的积分文件
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

def process_historical_data(df, cutoff_days=None):
    """
    处理历史数据，确保只保留指定天数内的数据（使用配置参数）
    """
    from datetime import datetime, timedelta

    # 如果没有指定天数，从配置中获取
    if cutoff_days is None:
        cutoff_days = config_manager.get('points_system.validity_days', 90)

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

        # 从配置中获取最小有效时长
        min_duration = config_manager.get('points_system.min_duration_minutes', 40)

        # 筛选大于等于配置时长的记录
        filtered_df = df[df['Duration'] >= min_duration].copy()

        if filtered_df.empty:
            return {
                'success': False,
                'error': f'没有找到持续时长大于等于{min_duration}分钟的直播记录'
            }

        # 提取日期信息（支持历史数据）
        filtered_df = extract_date_from_data(filtered_df)

        # 处理历史数据（过滤超过有效期的数据）
        validity_days = config_manager.get('points_system.validity_days', 90)
        filtered_df = process_historical_data(filtered_df)

        if filtered_df.empty:
            return {
                'success': False,
                'error': f'所有数据都超过了{validity_days}天有效期，无法获得积分'
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

        # 获取配置参数用于显示
        validity_days = config_manager.get('points_system.validity_days', 90)
        min_duration = config_manager.get('points_system.min_duration_minutes', 40)
        points_per_day = config_manager.get('points_system.points_per_day', 1)

        return render_template('index.html',
                             stats=stats,
                             validity_days=validity_days,
                             min_duration=min_duration,
                             points_per_day=points_per_day)
    except Exception as e:
        # 如果获取统计数据失败，仍然显示首页但不显示统计
        return render_template('index.html',
                             stats=None,
                             validity_days=90,
                             min_duration=40,
                             points_per_day=1)

# 管理员上传页面路由
@app.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def admin_upload():
    """
    管理员上传页面
    GET: 显示上传表单或处理筛选/分页
    POST: 处理文件上传
    """
    if request.method == 'GET':
        # 检查是否刚刚登录
        just_logged_in = session.pop('just_logged_in', False)
        current_user = get_current_user()

        # 检查是否需要清除session
        if request.args.get('clear_session'):
            session.pop('last_upload_result', None)
            return redirect(url_for('admin_upload'))

        # 检查是否有筛选参数，如果有则说明是在筛选结果
        has_filter_params = any([
            request.args.get('page'),
            request.args.get('per_page'),
            request.args.get('search_user_id'),
            request.args.get('search_user_name'),
            request.args.get('min_points'),
            request.args.get('max_points'),
            request.args.get('sort_by'),
            request.args.get('sort_order')
        ])

        # 如果有筛选参数且session中有上传结果数据，则处理筛选
        if has_filter_params and 'last_upload_result' in session:
            try:
                # 从session中获取上传结果数据
                last_result = session['last_upload_result']
                user_points = pd.DataFrame(last_result['user_points_data'])

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
                                         'filename': last_result['filename'],
                                         'total_users': last_result['total_users'],
                                         'user_points': filtered_user_points['data'],
                                         'total_records': filtered_user_points['total_records'],
                                         'total_pages': filtered_user_points['total_pages'],
                                         'current_page': page,
                                         'per_page': per_page,
                                         'general_qr': last_result.get('general_qr'),
                                         'upload_time': last_result['upload_time'],
                                         'search_params': {
                                             'search_user_id': search_user_id,
                                             'search_user_name': search_user_name,
                                             'min_points': min_points,
                                             'max_points': max_points,
                                             'sort_by': sort_by,
                                             'sort_order': sort_order
                                         }
                                     },
                                     current_user=current_user,
                                     min_duration=config_manager.get('points_system.min_duration_minutes', 40),
                                     points_per_day=config_manager.get('points_system.points_per_day', 1),
                                     validity_days=config_manager.get('points_system.validity_days', 90))
            except Exception as e:
                print(f"处理筛选参数失败: {str(e)}")
                # 如果处理失败，清除session数据并显示上传表单
                session.pop('last_upload_result', None)

        # 默认显示上传表单
        return render_template('admin_upload_combined.html',
                             show_results=False,
                             upload_result=None,
                             just_logged_in=just_logged_in,
                             current_user=current_user,
                             min_duration=config_manager.get('points_system.min_duration_minutes', 40),
                             points_per_day=config_manager.get('points_system.points_per_day', 1),
                             validity_days=config_manager.get('points_system.validity_days', 90))

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

                # 将上传结果保存到session中，以便后续筛选使用
                upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session['last_upload_result'] = {
                    'filename': filename,
                    'total_users': result['total_users'],
                    'user_points_data': user_points.to_dict('records'),  # 保存完整数据
                    'general_qr': general_qr_info,
                    'upload_time': upload_time
                }

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
                                         'upload_time': upload_time,
                                         'search_params': {
                                             'search_user_id': search_user_id,
                                             'search_user_name': search_user_name,
                                             'min_points': min_points,
                                             'max_points': max_points,
                                             'sort_by': sort_by,
                                             'sort_order': sort_order
                                         }
                                     },
                                     min_duration=config_manager.get('points_system.min_duration_minutes', 40),
                                     points_per_day=config_manager.get('points_system.points_per_day', 1),
                                     validity_days=config_manager.get('points_system.validity_days', 90))
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

            # 读取当前用户的历史记录数量
            points_history_file = get_user_data_path('points_history.csv')
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

# 清空用户积分功能
@app.route('/admin/clear_points', methods=['POST'])
@login_required
def clear_user_points():
    """
    清空用户积分功能
    支持清空单个用户或所有用户的积分
    """
    try:
        # 获取请求参数
        action = request.form.get('action')  # 'single' 或 'all'
        user_id = request.form.get('user_id', '').strip()
        confirm = request.form.get('confirm', '').lower()

        # 验证确认参数
        if confirm != 'yes':
            flash('请确认您要执行清空操作', 'error')
            return redirect(url_for('admin_points'))

        # 获取当前用户的数据文件路径
        user_points_file = get_user_data_path('user_points.csv')
        points_history_file = get_user_data_path('points_history.csv')

        if action == 'single' and user_id:
            # 清空单个用户的积分
            success = clear_single_user_points(user_id, user_points_file, points_history_file)
            if success:
                flash(f'用户 {user_id} 的积分已清空', 'success')
            else:
                flash(f'用户 {user_id} 不存在或清空失败', 'error')

        elif action == 'all':
            # 清空所有用户的积分
            success = clear_all_user_points(user_points_file, points_history_file)
            if success:
                flash('所有用户积分已清空', 'success')
            else:
                flash('清空所有用户积分失败', 'error')
        else:
            flash('无效的清空操作参数', 'error')

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"清空积分错误: {error_details}")
        flash(f'清空积分失败: {str(e)}', 'error')

    return redirect(url_for('admin_points'))

def clear_single_user_points(user_id, user_points_file, points_history_file):
    """
    清空单个用户的积分
    """
    try:
        # 处理用户积分统计文件
        if os.path.exists(user_points_file):
            user_stats = pd.read_csv(user_points_file)
            user_stats['UserID'] = user_stats['UserID'].astype(str)

            # 检查用户是否存在
            if user_id not in user_stats['UserID'].values:
                return False

            # 删除指定用户的记录
            user_stats = user_stats[user_stats['UserID'] != user_id]
            user_stats.to_csv(user_points_file, index=False)

        # 处理积分历史文件
        if os.path.exists(points_history_file):
            history_df = pd.read_csv(points_history_file)
            history_df['UserID'] = history_df['UserID'].astype(str)

            # 删除指定用户的历史记录
            history_df = history_df[history_df['UserID'] != user_id]
            history_df.to_csv(points_history_file, index=False)

        return True

    except Exception as e:
        print(f"清空单个用户积分错误: {str(e)}")
        return False

def clear_all_user_points(user_points_file, points_history_file):
    """
    清空所有用户的积分
    """
    try:
        # 清空用户积分统计文件
        if os.path.exists(user_points_file):
            # 创建空的DataFrame但保持列结构
            empty_df = pd.DataFrame(columns=['UserID', 'UserName', 'TotalPoints', 'ValidDays'])
            empty_df.to_csv(user_points_file, index=False)

        # 清空积分历史文件
        if os.path.exists(points_history_file):
            # 创建空的DataFrame但保持列结构
            empty_df = pd.DataFrame(columns=['UserID', 'Date', 'Points'])
            empty_df.to_csv(points_history_file, index=False)

        return True

    except Exception as e:
        print(f"清空所有用户积分错误: {str(e)}")
        return False

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

# 系统配置管理页面
@app.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    """
    系统配置管理页面
    """
    if request.method == 'GET':
        # 获取当前配置
        current_config = config_manager.config
        config_schema = config_manager.get_config_schema()
        current_user = get_current_user()

        return render_template('admin_config.html',
                             config=current_config,
                             schema=config_schema,
                             current_user=current_user)

    elif request.method == 'POST':
        try:
            # 获取表单数据
            updated_config = {}
            current_user = get_current_user()
            username = current_user['username'] if current_user else 'unknown'

            # 处理积分系统配置
            points_config = {}
            points_config['min_duration_minutes'] = int(request.form.get('min_duration_minutes', 40))
            points_config['points_per_day'] = int(request.form.get('points_per_day', 1))
            points_config['validity_days'] = int(request.form.get('validity_days', 90))
            points_config['allow_duplicate_daily'] = request.form.get('allow_duplicate_daily') == 'on'

            # 处理数据处理配置
            data_config = {}
            data_config['max_file_size_mb'] = int(request.form.get('max_file_size_mb', 50))
            data_config['auto_clean_uploads_days'] = int(request.form.get('auto_clean_uploads_days', 7))
            data_config['batch_size'] = int(request.form.get('batch_size', 1000))

            # 处理显示配置
            display_config = {}
            display_config['default_page_size'] = int(request.form.get('default_page_size', 10))
            display_config['max_page_size'] = int(request.form.get('max_page_size', 100))

            # 处理二维码系统配置
            qr_config = {}

            # 处理有效期配置（支持长期有效）
            # 检查是否选择了长期有效
            validity_type = request.form.get('validity_type', 'custom')
            if validity_type == 'permanent':
                # 长期有效
                qr_config['validity_hours'] = -1
                print("配置设置为长期有效")
            else:
                # 自定义有效期
                validity_hours = request.form.get('validity_hours', '24')
                try:
                    qr_config['validity_hours'] = int(validity_hours)
                    print(f"配置设置为自定义有效期: {qr_config['validity_hours']} 小时")
                except (ValueError, TypeError):
                    qr_config['validity_hours'] = 24
                    print("配置设置为默认有效期: 24 小时")

            qr_config['auto_clean_expired'] = request.form.get('auto_clean_expired') == 'on'
            qr_config['clean_interval_hours'] = int(request.form.get('clean_interval_hours', 6))
            qr_config['max_cache_size'] = int(request.form.get('max_cache_size', 1000))

            # 更新配置
            success_count = 0
            error_messages = []

            # 更新积分系统配置
            for key, value in points_config.items():
                if config_manager.set(f'points_system.{key}', value, username):
                    success_count += 1
                else:
                    error_messages.append(f'更新积分系统配置 {key} 失败')

            # 更新数据处理配置
            for key, value in data_config.items():
                if config_manager.set(f'data_processing.{key}', value, username):
                    success_count += 1
                else:
                    error_messages.append(f'更新数据处理配置 {key} 失败')

            # 更新显示配置
            for key, value in display_config.items():
                if config_manager.set(f'display.{key}', value, username):
                    success_count += 1
                else:
                    error_messages.append(f'更新显示配置 {key} 失败')

            # 更新二维码系统配置
            old_validity = config_manager.get('qr_system.validity_hours', 24)

            for key, value in qr_config.items():
                if config_manager.set(f'qr_system.{key}', value, username):
                    success_count += 1
                else:
                    error_messages.append(f'更新二维码系统配置 {key} 失败')

            # 如果有效期配置发生变化，处理现有缓存
            new_validity = qr_config.get('validity_hours', old_validity)
            if old_validity != new_validity:
                try:
                    handle_validity_config_change(old_validity, new_validity)
                    print(f"二维码有效期配置已从 {old_validity} 更改为 {new_validity}")
                except Exception as e:
                    print(f"处理有效期配置变更失败: {str(e)}")
                    error_messages.append('处理二维码缓存更新失败')

            # 验证配置
            validation_errors = config_manager.validate_config()
            if validation_errors:
                for category, errors in validation_errors.items():
                    for error in errors:
                        error_messages.append(f'{category}: {error}')

            # 显示结果
            if error_messages:
                flash(f'配置更新部分成功（{success_count}项），但有错误：' + '; '.join(error_messages), 'warning')
            else:
                flash(f'配置更新成功！共更新了{success_count}项配置', 'success')

            return redirect(url_for('admin_config'))

        except Exception as e:
            flash(f'配置更新失败: {str(e)}', 'error')
            return redirect(url_for('admin_config'))

# 生成通用二维码路由
@app.route('/admin/generate_universal_qr')
@login_required
def generate_universal_qr():
    """
    生成通用二维码，用户扫码后跳转到积分查询页面
    支持有效期和缓存机制
    """
    try:
        # 获取当前用户信息
        current_user = get_current_user()
        user_id = current_user['username'] if current_user else 'unknown'

        # 构建查询页面的完整URL
        base_url = request.url_root.rstrip('/')
        query_url = f"{base_url}/query"

        # 检查是否强制重新生成
        force_regenerate = request.args.get('force', 'false').lower() == 'true'

        # 检查是否已有有效的二维码（除非强制重新生成）
        if not force_regenerate:
            qr_cache_info = get_cached_universal_qr(user_id)

            if qr_cache_info and not is_qr_expired(qr_cache_info):
                # 返回缓存的二维码信息
                return jsonify({
                    'success': True,
                    'qr_url': qr_cache_info['qr_url'],
                    'query_url': query_url,
                    'expires_at': qr_cache_info['expires_at'],
                    'created_at': qr_cache_info['created_at'],
                    'is_cached': True,
                    'message': '使用已缓存的通用查询二维码'
                })
        else:
            print(f"用户 {user_id} 请求强制重新生成二维码")

        # 生成新的二维码
        qr_info = generate_general_qr_code(query_url)

        if qr_info:
            # 缓存二维码信息
            cache_info = cache_universal_qr(user_id, qr_info['web_path'], query_url)

            return jsonify({
                'success': True,
                'qr_url': qr_info['web_path'],
                'query_url': query_url,
                'expires_at': cache_info['expires_at'],
                'created_at': cache_info['created_at'],
                'is_cached': False,
                'message': '通用查询二维码生成成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '二维码生成失败'
            }), 500

    except Exception as e:
        print(f"生成通用二维码失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成二维码时出错: {str(e)}'
        }), 500

# 获取通用二维码状态路由
@app.route('/admin/universal_qr_status')
@login_required
def get_universal_qr_status():
    """
    获取当前用户的通用二维码状态
    """
    try:
        current_user = get_current_user()
        user_id = current_user['username'] if current_user else 'unknown'

        # 构建查询页面的完整URL
        base_url = request.url_root.rstrip('/')
        query_url = f"{base_url}/query"

        # 检查缓存的二维码
        qr_cache_info = get_cached_universal_qr(user_id)

        if qr_cache_info and not is_qr_expired(qr_cache_info):
            return jsonify({
                'success': True,
                'has_valid_qr': True,
                'qr_url': qr_cache_info['qr_url'],
                'query_url': query_url,
                'expires_at': qr_cache_info['expires_at'],
                'created_at': qr_cache_info['created_at']
            })
        else:
            return jsonify({
                'success': True,
                'has_valid_qr': False,
                'message': '没有有效的二维码缓存'
            })

    except Exception as e:
        print(f"获取二维码状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态时出错: {str(e)}'
        }), 500

# 二维码缓存管理函数
def get_qr_cache_file_path():
    """获取二维码缓存文件路径"""
    return os.path.join('data', 'universal_qr_cache.json')

def ensure_qr_cache_dir():
    """确保缓存目录存在"""
    cache_dir = os.path.dirname(get_qr_cache_file_path())
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def load_qr_cache():
    """加载二维码缓存"""
    try:
        cache_file = get_qr_cache_file_path()
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"加载二维码缓存失败: {str(e)}")
        return {}

def save_qr_cache(cache_data):
    """保存二维码缓存"""
    try:
        ensure_qr_cache_dir()
        cache_file = get_qr_cache_file_path()
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存二维码缓存失败: {str(e)}")
        return False

def get_cached_universal_qr(user_id):
    """获取用户的缓存二维码信息"""
    try:
        cache_data = load_qr_cache()
        cached_qr = cache_data.get(user_id)

        if not cached_qr:
            return None

        # 检查缓存的配置是否与当前配置兼容
        current_validity = config_manager.get('qr_system.validity_hours', 24)
        cached_validity = cached_qr.get('validity_hours', 24)

        # 如果配置发生变化，需要重新验证缓存
        if current_validity != cached_validity:
            print(f"配置已变更，当前有效期: {current_validity}，缓存有效期: {cached_validity}")

            # 如果当前配置是长期有效，但缓存不是，需要更新缓存
            if current_validity == -1 and cached_validity != -1:
                print("配置已改为长期有效，更新缓存...")
                # 更新缓存为长期有效
                cached_qr['validity_hours'] = -1
                cached_qr['expires_at'] = "永不过期"

                # 保存更新后的缓存
                cache_data[user_id] = cached_qr
                save_qr_cache(cache_data)

                return cached_qr

            # 如果当前配置不是长期有效，但缓存是长期有效，需要重新生成
            elif current_validity != -1 and cached_validity == -1:
                print("配置已改为自定义有效期，需要重新生成...")
                return None

            # 如果都是自定义有效期但时长不同，检查是否仍在有效期内
            elif current_validity != -1 and cached_validity != -1:
                # 重新计算过期时间
                try:
                    created_at = datetime.fromisoformat(cached_qr['created_at'])
                    new_expires_at = created_at + timedelta(hours=current_validity)

                    if datetime.now() <= new_expires_at:
                        # 仍在新的有效期内，更新缓存
                        cached_qr['validity_hours'] = current_validity
                        cached_qr['expires_at'] = new_expires_at.isoformat()

                        cache_data[user_id] = cached_qr
                        save_qr_cache(cache_data)

                        return cached_qr
                    else:
                        # 已超过新的有效期，需要重新生成
                        print("根据新配置，缓存已过期，需要重新生成...")
                        return None
                except Exception as e:
                    print(f"重新计算有效期失败: {str(e)}")
                    return None

        return cached_qr

    except Exception as e:
        print(f"获取缓存二维码失败: {str(e)}")
        return None

def cache_universal_qr(user_id, qr_url, query_url, validity_hours=None):
    """缓存用户的二维码信息"""
    try:
        # 从配置中获取有效期，默认24小时
        if validity_hours is None:
            validity_hours = config_manager.get('qr_system.validity_hours', 24)

        current_time = datetime.now()

        # 处理长期有效的情况
        if validity_hours == -1:
            # 长期有效，设置为100年后过期（实际上永不过期）
            expires_at = current_time + timedelta(days=36500)
            expires_at_str = "永不过期"
        else:
            expires_at = current_time + timedelta(hours=validity_hours)
            expires_at_str = expires_at.isoformat()

        cache_info = {
            'qr_url': qr_url,
            'query_url': query_url,
            'created_at': current_time.isoformat(),
            'expires_at': expires_at_str,
            'validity_hours': validity_hours
        }

        # 加载现有缓存
        cache_data = load_qr_cache()
        cache_data[user_id] = cache_info

        # 保存缓存
        if save_qr_cache(cache_data):
            return cache_info
        else:
            return None

    except Exception as e:
        print(f"缓存二维码失败: {str(e)}")
        return None

def is_qr_expired(qr_cache_info):
    """检查二维码是否已过期"""
    try:
        if not qr_cache_info or 'expires_at' not in qr_cache_info:
            return True

        expires_at_str = qr_cache_info['expires_at']

        # 检查是否为长期有效
        if expires_at_str == "永不过期":
            return False

        # 检查有效期小时数
        validity_hours = qr_cache_info.get('validity_hours', 24)
        if validity_hours == -1:
            return False

        expires_at = datetime.fromisoformat(expires_at_str)
        return datetime.now() > expires_at

    except Exception as e:
        print(f"检查二维码过期状态失败: {str(e)}")
        return True

def clean_expired_qr_cache():
    """清理过期的二维码缓存"""
    try:
        cache_data = load_qr_cache()
        cleaned_data = {}
        cleaned_count = 0

        for user_id, qr_info in cache_data.items():
            if not is_qr_expired(qr_info):
                cleaned_data[user_id] = qr_info
            else:
                cleaned_count += 1

        if cleaned_count > 0:
            save_qr_cache(cleaned_data)
            print(f"清理了 {cleaned_count} 个过期的二维码缓存")

        return cleaned_count

    except Exception as e:
        print(f"清理过期缓存失败: {str(e)}")
        return 0

def handle_validity_config_change(old_validity, new_validity):
    """处理有效期配置变更"""
    try:
        cache_data = load_qr_cache()
        updated_data = {}
        updated_count = 0
        removed_count = 0

        print(f"处理有效期配置变更: {old_validity} -> {new_validity}")

        for user_id, qr_info in cache_data.items():
            try:
                # 如果新配置是长期有效
                if new_validity == -1:
                    # 将所有缓存更新为长期有效
                    qr_info['validity_hours'] = -1
                    qr_info['expires_at'] = "永不过期"
                    updated_data[user_id] = qr_info
                    updated_count += 1
                    print(f"用户 {user_id} 的二维码已更新为长期有效")

                # 如果新配置是自定义有效期
                elif new_validity > 0:
                    # 重新计算过期时间
                    created_at = datetime.fromisoformat(qr_info['created_at'])
                    new_expires_at = created_at + timedelta(hours=new_validity)

                    # 检查是否仍在新的有效期内
                    if datetime.now() <= new_expires_at:
                        # 更新缓存
                        qr_info['validity_hours'] = new_validity
                        qr_info['expires_at'] = new_expires_at.isoformat()
                        updated_data[user_id] = qr_info
                        updated_count += 1
                        print(f"用户 {user_id} 的二维码有效期已更新为 {new_validity} 小时")
                    else:
                        # 已过期，移除缓存
                        removed_count += 1
                        print(f"用户 {user_id} 的二维码根据新配置已过期，已移除缓存")

                else:
                    # 无效的配置，移除缓存
                    removed_count += 1
                    print(f"用户 {user_id} 的二维码因无效配置被移除")

            except Exception as e:
                print(f"处理用户 {user_id} 的缓存时出错: {str(e)}")
                # 出错时移除该缓存
                removed_count += 1

        # 保存更新后的缓存
        if save_qr_cache(updated_data):
            print(f"配置变更处理完成: 更新了 {updated_count} 个缓存，移除了 {removed_count} 个缓存")
        else:
            print("保存更新后的缓存失败")

        return updated_count, removed_count

    except Exception as e:
        print(f"处理有效期配置变更失败: {str(e)}")
        return 0, 0

# 运行应用
if __name__ == '__main__':
    # 开启调试模式，方便开发
    app.run(debug=True, host='0.0.0.0', port=5000)
