#!/usr/bin/env python3
"""监控知识图谱生成进度的脚本"""

import time
import re
import os

def monitor_progress():
    """监控处理进度"""
    log_file = "processing.log"
    
    if not os.path.exists(log_file):
        print("❌ 日志文件不存在")
        return
    
    print("🔍 监控知识图谱生成进度...")
    print("=" * 50)
    
    last_size = 0
    last_chunk = 0
    
    while True:
        try:
            # 检查文件大小变化
            current_size = os.path.getsize(log_file)
            
            if current_size > last_size:
                # 读取最新内容
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找处理进度
                chunk_matches = re.findall(r'Processing chunk (\d+)/(\d+)', content)
                if chunk_matches:
                    current_chunk, total_chunks = chunk_matches[-1]
                    current_chunk = int(current_chunk)
                    total_chunks = int(total_chunks)
                    
                    if current_chunk > last_chunk:
                        progress = (current_chunk / total_chunks) * 100
                        print(f"📊 进度: {current_chunk}/{total_chunks} ({progress:.1f}%)")
                        last_chunk = current_chunk
                
                # 查找阶段信息
                if "PHASE 1: INITIAL TRIPLE EXTRACTION" in content:
                    print("🔄 阶段1: 初始三元组提取")
                elif "PHASE 2: ENTITY STANDARDIZATION" in content:
                    print("🔄 阶段2: 实体标准化")
                elif "PHASE 3: RELATIONSHIP INFERENCE" in content:
                    print("🔄 阶段3: 关系推理")
                elif "Knowledge graph visualization saved" in content:
                    print("✅ 知识图谱生成完成！")
                    break
                
                last_size = current_size
            
            # 检查进程是否还在运行
            import subprocess
            try:
                result = subprocess.run(['pgrep', '-f', 'generate-graph.py'], 
                                      capture_output=True, text=True)
                if not result.stdout.strip():
                    print("⚠️  进程已结束")
                    break
            except:
                pass
            
            time.sleep(10)  # 每10秒检查一次
            
        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控出错: {e}")
            break

if __name__ == "__main__":
    monitor_progress()