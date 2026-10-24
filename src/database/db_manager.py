#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý dữ liệu cho SharinganV2
"""

import os
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional, Tuple


class DBManager:
    """Lớp quản lý cơ sở dữ liệu cho SharinganV2"""
    
    def __init__(self, db_file: str = "sharingan.db"):
        """
        Khởi tạo lớp quản lý cơ sở dữ liệu
        
        Args:
            db_file: Đường dẫn đến tệp cơ sở dữ liệu
        """
        self.db_file = db_file
        self._init_db()
    
    def _init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tạo bảng targets
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            scan_date TIMESTAMP NOT NULL,
            url_count INTEGER DEFAULT 0,
            param_url_count INTEGER DEFAULT 0,
            vuln_count INTEGER DEFAULT 0
        )
        ''')
        
        # Tạo bảng urls
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            url TEXT NOT NULL,
            has_params INTEGER DEFAULT 0,
            source TEXT,
            FOREIGN KEY (target_id) REFERENCES targets (id)
        )
        ''')
        
        # Tạo bảng vulnerabilities
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            url_id INTEGER,
            type TEXT NOT NULL,
            param TEXT,
            payload TEXT,
            evidence TEXT,
            severity TEXT DEFAULT 'info',
            FOREIGN KEY (target_id) REFERENCES targets (id),
            FOREIGN KEY (url_id) REFERENCES urls (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_target(self, target: str) -> int:
        """
        Thêm mục tiêu mới vào cơ sở dữ liệu
        
        Args:
            target: Tên miền mục tiêu
            
        Returns:
            int: ID của mục tiêu vừa thêm
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO targets (name, scan_date)
        VALUES (?, ?)
        ''', (target, time.time()))
        
        target_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return target_id
    
    def add_urls(self, target_id: int, urls: List[str], source: str, has_params: bool = False) -> None:
        """
        Thêm danh sách URL vào cơ sở dữ liệu
        
        Args:
            target_id: ID của mục tiêu
            urls: Danh sách URL
            source: Nguồn URL (paramspider, waybackurls, ...)
            has_params: URL có tham số hay không
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for url in urls:
            cursor.execute('''
            INSERT INTO urls (target_id, url, has_params, source)
            VALUES (?, ?, ?, ?)
            ''', (target_id, url, 1 if has_params else 0, source))
        
        # Cập nhật số lượng URL trong bảng targets
        cursor.execute('''
        UPDATE targets
        SET url_count = url_count + ?,
            param_url_count = param_url_count + ?
        WHERE id = ?
        ''', (len(urls), len(urls) if has_params else 0, target_id))
        
        conn.commit()
        conn.close()
    
    def add_vulnerability(self, target_id: int, url: str, vuln_type: str,
                        param: str, payload: str, evidence: str, severity: str = "info") -> None:
        """
        Thêm lỗ hổng vào cơ sở dữ liệu
        
        Args:
            target_id: ID của mục tiêu
            url: URL có lỗ hổng
            vuln_type: Loại lỗ hổng
            param: Tham số có lỗ hổng
            payload: Payload khai thác
            evidence: Bằng chứng lỗ hổng
            severity: Mức độ nghiêm trọng (high, medium, low, info)
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tìm url_id
        cursor.execute('''
        SELECT id FROM urls
        WHERE target_id = ? AND url = ?
        ''', (target_id, url))
        
        result = cursor.fetchone()
        if result:
            url_id = result[0]
        else:
            # URL chưa tồn tại, thêm mới
            cursor.execute('''
            INSERT INTO urls (target_id, url, has_params)
            VALUES (?, ?, 1)
            ''', (target_id, url))
            url_id = cursor.lastrowid
        
        # Thêm lỗ hổng
        cursor.execute('''
        INSERT INTO vulnerabilities (target_id, url_id, type, param, payload, evidence, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (target_id, url_id, vuln_type, param, payload, evidence, severity))
        
        # Cập nhật số lượng lỗ hổng trong bảng targets
        cursor.execute('''
        UPDATE targets
        SET vuln_count = vuln_count + 1
        WHERE id = ?
        ''', (target_id,))
        
        conn.commit()
        conn.close()
    
    def get_target_info(self, target_id: int) -> Optional[Dict]:
        """
        Lấy thông tin về mục tiêu
        
        Args:
            target_id: ID của mục tiêu
            
        Returns:
            Dict: Thông tin về mục tiêu hoặc None nếu không tìm thấy
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, scan_date, url_count, param_url_count, vuln_count
        FROM targets
        WHERE id = ?
        ''', (target_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "scan_date": result[2],
                "url_count": result[3],
                "param_url_count": result[4],
                "vuln_count": result[5]
            }
        
        return None
    
    def get_target_vulnerabilities(self, target_id: int) -> List[Dict]:
        """
        Lấy danh sách lỗ hổng của mục tiêu
        
        Args:
            target_id: ID của mục tiêu
            
        Returns:
            List[Dict]: Danh sách lỗ hổng
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT v.id, u.url, v.type, v.param, v.payload, v.evidence, v.severity
        FROM vulnerabilities v
        JOIN urls u ON v.url_id = u.id
        WHERE v.target_id = ?
        ORDER BY 
            CASE v.severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END
        ''', (target_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        vulnerabilities = []
        for result in results:
            vulnerabilities.append({
                "id": result[0],
                "url": result[1],
                "vulnerability_type": result[2],
                "param": result[3],
                "payload": result[4],
                "evidence": result[5],
                "severity": result[6]
            })
        
        return vulnerabilities
    
    def get_recent_scans(self, limit: int = 10) -> List[Dict]:
        """
        Lấy danh sách các lần quét gần đây
        
        Args:
            limit: Số lượng kết quả tối đa
            
        Returns:
            List[Dict]: Danh sách các lần quét
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, scan_date, url_count, param_url_count, vuln_count
        FROM targets
        ORDER BY scan_date DESC
        LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        scans = []
        for result in results:
            scans.append({
                "id": result[0],
                "name": result[1],
                "scan_date": result[2],
                "url_count": result[3],
                "param_url_count": result[4],
                "vuln_count": result[5]
            })
        
        return scans