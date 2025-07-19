from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
from datetime import datetime

# 安全导入 qrcode 模块
import sys
current_dir = os.getcwd()
if current_dir in sys.path:
    sys.path.remove(current_dir)

import qrcode

# 创建 Flask 应用实例
app = Flask(__name__)

# 设置密钥用于 flash 消息
app.secret_key = 'your-secret-key-here'

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
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

def process_points_accumulation(new_points, daily_stats):
    """
    处理积分累计和90天过期机制
    """
    from datetime import datetime, timedelta

    # 当前日期
    current_date = datetime.now().date()
    cutoff_date = current_date - timedelta(days=90)

    # 读取历史积分记录
    points_history_file = 'points_history.csv'
    if os.path.exists(points_history_file):
        history_df = pd.read_csv(points_history_file)
        history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
        history_df['UserID'] = history_df['UserID'].astype(str)
    else:
        # 创建空的历史记录
        history_df = pd.DataFrame(columns=['UserID', 'Date', 'Points'])

    # 添加新的积分记录
    new_records = []
    for _, row in daily_stats.iterrows():
        new_records.append({
            'UserID': str(row['UserID']),
            'Date': row['Date'],
            'Points': 1  # 每天最多1分
        })

    if new_records:
        new_df = pd.DataFrame(new_records)
        history_df = pd.concat([history_df, new_df], ignore_index=True)

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

    # 保存当前积分文件
    user_points.to_csv('user_points.csv', index=False)

    return user_points

def process_uploaded_file(file_path):
    """
    处理上传的文件，支持 CSV、Excel 等格式，计算积分
    """
    try:
        # 根据文件扩展名选择读取方法
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension == '.json':
            df = pd.read_json(file_path)
        elif file_extension == '.tsv':
            df = pd.read_csv(file_path, sep='\t')
        else:
            return {
                'success': False,
                'error': f'不支持的文件格式: {file_extension}。支持的格式: .csv, .xlsx, .xls, .json, .tsv'
            }

        # 检查必要的列
        required_columns = ['UserID', 'StartTime', 'EndTime']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'success': False,
                'error': f'文件缺少必要的列: {", ".join(missing_columns)}。需要包含: UserID, StartTime, EndTime'
            }

        # 处理数据
        df['StartTime'] = pd.to_datetime(df['StartTime'])
        df['EndTime'] = pd.to_datetime(df['EndTime'])
        df['UserID'] = df['UserID'].astype(str)
        df['Duration'] = (df['EndTime'] - df['StartTime']).dt.total_seconds() / 60

        # 筛选大于40分钟的记录
        filtered_df = df[df['Duration'] > 40].copy()

        if filtered_df.empty:
            return {
                'success': False,
                'error': '没有找到持续时长大于40分钟的直播记录'
            }

        # 计算新增积分（每个用户每天最多1分）
        filtered_df['Date'] = filtered_df['StartTime'].dt.date
        daily_stats = filtered_df.groupby(['UserID', 'Date']).size().reset_index(name='Count')
        new_points = daily_stats.groupby('UserID').size().reset_index(name='NewPoints')
        new_points['UserID'] = new_points['UserID'].astype(str)

        # 处理积分累计和过期
        user_points = process_points_accumulation(new_points, daily_stats)

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
@app.route('/')
def home():
    """
    主页路由
    返回系统启动信息
    """
    return "积分查询系统已启动！"

# 管理员上传页面路由
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    """
    管理员上传页面
    GET: 显示上传表单
    POST: 处理文件上传
    """
    if request.method == 'GET':
        # 渲染上传页面模板
        return render_template('upload.html')

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

                flash(f'处理成功！共 {result["total_users"]} 个用户数据已处理', 'success')

                return render_template('upload_success.html',
                                     filename=filename,
                                     total_users=result['total_users'],
                                     user_points=user_points,
                                     general_qr=general_qr_info,
                                     upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            else:
                flash(f'处理失败: {result["error"]}', 'error')
                return redirect(request.url)
        else:
            flash(f'不支持的文件格式。支持的格式: {", ".join(allowed_extensions)}', 'error')
            return redirect(request.url)

# 积分管理页面
@app.route('/admin/points')
def admin_points():
    """
    积分管理页面，查看积分历史和过期情况
    """
    try:
        from datetime import datetime, timedelta

        # 读取积分历史
        points_history_file = 'points_history.csv'
        if os.path.exists(points_history_file):
            history_df = pd.read_csv(points_history_file)
            history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
            history_df['UserID'] = history_df['UserID'].astype(str)

            # 计算过期信息
            current_date = datetime.now().date()
            history_df['DaysLeft'] = history_df['Date'].apply(
                lambda x: max(0, 90 - (current_date - x).days)
            )

            # 按用户分组统计
            user_stats = history_df.groupby('UserID').agg({
                'Points': 'sum',
                'Date': ['count', 'min', 'max'],
                'DaysLeft': 'min'
            }).round(2)

            user_stats.columns = ['总积分', '有效天数', '首次获得', '最近获得', '最快过期']
            user_stats = user_stats.reset_index()

            return render_template('admin_points.html',
                                 user_stats=user_stats,
                                 history_count=len(history_df),
                                 current_date=current_date)
        else:
            return render_template('admin_points.html',
                                 user_stats=pd.DataFrame(),
                                 history_count=0,
                                 current_date=datetime.now().date())
    except Exception as e:
        flash(f'读取积分数据失败: {str(e)}', 'error')
        return redirect(url_for('admin_upload'))

# 通用查询页面
@app.route('/query')
def query_page():
    """
    通用查询页面，用户可以输入用户ID查询积分
    """
    return render_template('query_page.html')

# 用户查询接口
@app.route('/query/<user_id>')
def query_user(user_id):
    """
    用户查询接口
    """
    try:
        if not os.path.exists('user_points.csv'):
            return render_template('query_result.html',
                                 user_id=user_id,
                                 error_message="积分数据文件不存在，请先上传数据文件")

        df = pd.read_csv('user_points.csv')
        df['UserID'] = df['UserID'].astype(str)

        # 尝试多种格式查找用户
        user_record = df[df['UserID'] == str(user_id).zfill(3)]
        if user_record.empty:
            user_record = df[df['UserID'] == str(user_id)]

        if not user_record.empty:
            total_points = user_record['TotalPoints'].iloc[0]
            return render_template('query_result.html',
                                 user_id=user_id,
                                 total_points=total_points,
                                 found=True)
        else:
            return render_template('query_result.html',
                                 user_id=user_id,
                                 error_message="未查询到该用户信息",
                                 found=False)

    except Exception as e:
        return render_template('query_result.html',
                             user_id=user_id,
                             error_message=f"查询错误：{str(e)}")

# 运行应用
if __name__ == '__main__':
    # 开启调试模式，方便开发
    app.run(debug=True, host='0.0.0.0', port=5000)
