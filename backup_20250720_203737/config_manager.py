#!/usr/bin/env python3
"""
配置管理模块
管理系统的可配置参数，如有效时长、积分值、有效期等
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'system_config.json'):
        self.config_file = config_file
        self.default_config = {
            # 积分系统配置
            'points_system': {
                'min_duration_minutes': 40,      # 最小有效时长（分钟）
                'points_per_day': 1,             # 每天可获得的积分
                'validity_days': 90,             # 积分有效期（天）
                'allow_duplicate_daily': False   # 是否允许同一天多次获得积分
            },
            
            # 数据处理配置
            'data_processing': {
                'max_file_size_mb': 50,          # 最大文件大小（MB）
                'supported_formats': ['.csv', '.xlsx', '.xls', '.json', '.tsv'],
                'auto_clean_uploads_days': 7,    # 自动清理上传文件的天数
                'batch_size': 1000               # 批处理大小
            },
            
            # 显示配置
            'display': {
                'default_page_size': 10,         # 默认分页大小
                'max_page_size': 100,            # 最大分页大小
                'date_format': '%Y-%m-%d',       # 日期显示格式
                'datetime_format': '%Y-%m-%d %H:%M:%S'  # 日期时间显示格式
            },
            
            # 二维码系统配置
            'qr_system': {
                'validity_hours': 24,            # 二维码有效期（小时）
                'auto_clean_expired': True,      # 是否自动清理过期二维码
                'clean_interval_hours': 6,       # 清理间隔（小时）
                'max_cache_size': 1000          # 最大缓存数量
            },

            # 系统配置
            'system': {
                'session_timeout_hours': 24,     # 会话超时时间（小时）
                'max_login_attempts': 5,         # 最大登录尝试次数
                'enable_registration': True,     # 是否允许注册
                'debug_mode': False              # 调试模式
            },
            
            # 配置元信息
            'meta': {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'updated_by': 'system'
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置（确保新增的配置项不会丢失）
                merged_config = self._merge_config(self.default_config, config)
                
                # 如果配置有更新，保存合并后的配置
                if merged_config != config:
                    self.save_config(merged_config)
                
                return merged_config
            else:
                # 配置文件不存在，创建默认配置
                self.save_config(self.default_config)
                return self.default_config.copy()
        
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {str(e)}")
            print("使用默认配置")
            return self.default_config.copy()
    
    def _merge_config(self, default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置，确保默认配置项不会丢失"""
        merged = current.copy()
        
        for key, value in default.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self._merge_config(value, merged[key])
        
        return merged
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置文件"""
        try:
            config_to_save = config if config is not None else self.config
            
            # 更新元信息
            config_to_save['meta']['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的配置
            if config is not None:
                self.config = config
            
            return True
        
        except Exception as e:
            print(f"❌ 保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        key_path: 配置路径，如 'points_system.min_duration_minutes'
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                value = value[key]
            
            return value
        
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, updated_by: str = 'admin') -> bool:
        """
        设置配置值
        key_path: 配置路径，如 'points_system.min_duration_minutes'
        value: 新值
        updated_by: 更新者
        """
        try:
            keys = key_path.split('.')
            config = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置值
            config[keys[-1]] = value
            
            # 更新元信息
            self.config['meta']['updated_by'] = updated_by
            
            # 保存配置
            return self.save_config()
        
        except Exception as e:
            print(f"❌ 设置配置失败: {str(e)}")
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """验证配置的合理性"""
        errors = {}
        
        # 验证积分系统配置
        points_config = self.config.get('points_system', {})
        
        if points_config.get('min_duration_minutes', 0) <= 0:
            errors.setdefault('points_system', []).append('最小有效时长必须大于0')
        
        if points_config.get('points_per_day', 0) <= 0:
            errors.setdefault('points_system', []).append('每日积分必须大于0')
        
        if points_config.get('validity_days', 0) <= 0:
            errors.setdefault('points_system', []).append('积分有效期必须大于0')
        
        # 验证数据处理配置
        data_config = self.config.get('data_processing', {})
        
        if data_config.get('max_file_size_mb', 0) <= 0:
            errors.setdefault('data_processing', []).append('最大文件大小必须大于0')
        
        if data_config.get('batch_size', 0) <= 0:
            errors.setdefault('data_processing', []).append('批处理大小必须大于0')
        
        # 验证显示配置
        display_config = self.config.get('display', {})

        if display_config.get('default_page_size', 0) <= 0:
            errors.setdefault('display', []).append('默认分页大小必须大于0')

        if display_config.get('max_page_size', 0) <= 0:
            errors.setdefault('display', []).append('最大分页大小必须大于0')

        # 验证二维码系统配置
        qr_config = self.config.get('qr_system', {})

        validity_hours = qr_config.get('validity_hours', 0)
        # -1 表示长期有效，是合法值
        if validity_hours != -1 and validity_hours <= 0:
            errors.setdefault('qr_system', []).append('二维码有效期必须大于0小时或设置为长期有效')

        if validity_hours > 8760:  # 1年
            errors.setdefault('qr_system', []).append('二维码有效期不能超过8760小时（1年）')

        if qr_config.get('clean_interval_hours', 0) <= 0:
            errors.setdefault('qr_system', []).append('清理间隔必须大于0小时')

        if qr_config.get('max_cache_size', 0) <= 0:
            errors.setdefault('qr_system', []).append('最大缓存数量必须大于0')

        return errors
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置项的描述信息"""
        return {
            'points_system': {
                'title': '积分系统配置',
                'fields': {
                    'min_duration_minutes': {
                        'title': '最小有效时长',
                        'description': '用户观看直播的最小时长（分钟），达到此时长才能获得积分',
                        'type': 'number',
                        'min': 1,
                        'max': 1440,  # 24小时
                        'unit': '分钟'
                    },
                    'points_per_day': {
                        'title': '每日积分',
                        'description': '用户每天最多可获得的积分数',
                        'type': 'number',
                        'min': 1,
                        'max': 100,
                        'unit': '分'
                    },
                    'validity_days': {
                        'title': '积分有效期',
                        'description': '积分的有效期，超过此期限的积分将被清除',
                        'type': 'number',
                        'min': 1,
                        'max': 3650,  # 10年
                        'unit': '天'
                    },
                    'allow_duplicate_daily': {
                        'title': '允许同日多次积分',
                        'description': '是否允许用户在同一天多次获得积分',
                        'type': 'boolean'
                    }
                }
            },
            'data_processing': {
                'title': '数据处理配置',
                'fields': {
                    'max_file_size_mb': {
                        'title': '最大文件大小',
                        'description': '允许上传的最大文件大小',
                        'type': 'number',
                        'min': 1,
                        'max': 1024,  # 1GB
                        'unit': 'MB'
                    },
                    'auto_clean_uploads_days': {
                        'title': '自动清理上传文件',
                        'description': '自动清理上传文件的天数',
                        'type': 'number',
                        'min': 1,
                        'max': 365,
                        'unit': '天'
                    },
                    'batch_size': {
                        'title': '批处理大小',
                        'description': '数据处理时的批次大小',
                        'type': 'number',
                        'min': 100,
                        'max': 10000,
                        'unit': '条'
                    }
                }
            },
            'display': {
                'title': '显示配置',
                'fields': {
                    'default_page_size': {
                        'title': '默认分页大小',
                        'description': '列表页面默认显示的记录数',
                        'type': 'number',
                        'min': 5,
                        'max': 100,
                        'unit': '条'
                    },
                    'max_page_size': {
                        'title': '最大分页大小',
                        'description': '列表页面最多显示的记录数',
                        'type': 'number',
                        'min': 10,
                        'max': 1000,
                        'unit': '条'
                    }
                }
            },
            'qr_system': {
                'title': '二维码系统配置',
                'fields': {
                    'validity_hours': {
                        'title': '二维码有效期',
                        'description': '通用二维码的有效时长。可选择长期有效或自定义小时数',
                        'type': 'number',
                        'min': 1,
                        'max': 8760,
                        'unit': '小时'
                    },
                    'auto_clean_expired': {
                        'title': '自动清理过期二维码',
                        'description': '是否自动清理过期的二维码缓存',
                        'type': 'boolean'
                    },
                    'clean_interval_hours': {
                        'title': '清理间隔',
                        'description': '自动清理过期二维码的时间间隔',
                        'type': 'number',
                        'min': 1,
                        'max': 24,
                        'unit': '小时'
                    },
                    'max_cache_size': {
                        'title': '最大缓存数量',
                        'description': '系统最多缓存的二维码数量',
                        'type': 'number',
                        'min': 10,
                        'max': 10000,
                        'unit': '个'
                    }
                }
            }
        }

# 全局配置管理器实例
config_manager = ConfigManager()
