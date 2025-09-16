#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AartFlow Blender 插件
提供艺术渲染、对象测量、数据绘图等功能
"""

bl_info = {
    "name": "AartFlow",
    "author": "AartFlow Team",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AartFlow",
    "description": "AartFlow 艺术渲染和测量工具集",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

import bpy
from . import AARTFLOW_integration

# 需要注册的类列表
classes = []

def register():
    """注册插件"""
    # 通过 AARTFLOW_integration 注册所有功能
    if hasattr(AARTFLOW_integration, 'register'):
        AARTFLOW_integration.register()
    
    print("AartFlow 插件已注册")

def unregister():
    """注销插件"""
    # 通过 AARTFLOW_integration 注销所有功能
    if hasattr(AARTFLOW_integration, 'unregister'):
        try:
            AARTFLOW_integration.unregister()
        except:
            pass
    
    print("AartFlow 插件已注销")

if __name__ == "__main__":
    register()
