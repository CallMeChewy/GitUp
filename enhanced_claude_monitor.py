#!/usr/bin/env python3
"""
Enhanced Claude Auto-Monitor System with Chat History Capture
Automatically captures Claude CLI sessions AND conversation history for restoration.
"""

import os
import sys
import json
import time
import psutil
import signal
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
import glob
import hashlib

class ClaudeAutoMonitor:
    def __init__(self, project_dir=None, auto_save_interval=30):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.auto_save_interval = auto_save_interval
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Archive setup
        self.archive_dir = self.project_dir / "ClaudeHistory" / "AutoArchives"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Claude storage paths
        self.claude_cache = Path.home() / ".cache" / "claude-cli-nodejs"
        self.claude_projects = Path.home() / ".claude" / "projects"
        self.last_capture_time = datetime.now()
        
        # Chat history tracking
        self.conversation_files = {}
        self.last_conversation_hashes = {}
        
        # State tracking
        self.claude_processes = {}
        self.is_monitoring = False
        self.auto_save_thread = None
        self.process_monitor_thread = None
        self.mcp_observer = None
        self.chat_observer = None
        
        # Emergency handlers
        signal.signal(signal.SIGINT, self._emergency_save)
        signal.signal(signal.SIGTERM, self._emergency_save)
        
        print(f"🤖 Enhanced Claude Auto-Monitor initialized")
        print(f"📁 Project: {self.project_dir}")
        print(f"💾 Session: {self.session_id}")
        print(f"⏰ Auto-save: every {auto_save_interval}s")
        print(f"💬 Chat tracking: {self.claude_projects}")

    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.is_monitoring:
            print("⚠️  Already monitoring")
            return
            
        self.is_monitoring = True
        print("🚀 Starting enhanced auto-monitoring...")
        
        # Start process monitoring
        self.process_monitor_thread = threading.Thread(
            target=self._monitor_claude_processes,
            daemon=True
        )
        self.process_monitor_thread.start()
        
        # Start auto-save thread
        self.auto_save_thread = threading.Thread(
            target=self._auto_save_loop,
            daemon=True
        )
        self.auto_save_thread.start()
        
        # Start MCP log monitoring
        self._start_mcp_monitoring()
        
        # Start chat history monitoring
        self._start_chat_monitoring()
        
        print("✅ Enhanced auto-monitoring active")
        print("💡 Run 'claude' in another terminal - I'll capture everything")

    def _start_chat_monitoring(self):
        """Monitor Claude conversation files"""
        if not self.claude_projects.exists():
            print("⚠️  Claude projects directory not found")
            return
            
        try:
            class ChatHistoryHandler(FileSystemEventHandler):
                def __init__(self, monitor):
                    self.monitor = monitor
                    
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith('.jsonl'):
                        self.monitor._on_conversation_change(event.src_path)
            
            self.chat_observer = Observer()
            self.chat_observer.schedule(
                ChatHistoryHandler(self),
                str(self.claude_projects),
                recursive=True
            )
            self.chat_observer.start()
            print("💬 Chat history monitoring started")
            
        except Exception as e:
            print(f"⚠️  Chat monitoring setup failed: {e}")

    def _on_conversation_change(self, jsonl_path):
        """Handle conversation file changes"""
        try:
            # Get file hash to detect actual changes
            with open(jsonl_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            if jsonl_path not in self.last_conversation_hashes:
                print(f"💬 New conversation detected: {Path(jsonl_path).name}")
            elif self.last_conversation_hashes[jsonl_path] != file_hash:
                print(f"💬 Conversation updated: {Path(jsonl_path).name}")
                # Auto-capture on significant conversation changes
                self._capture_current_state("conversation_update")
            
            self.last_conversation_hashes[jsonl_path] = file_hash
            
        except Exception as e:
            print(f"⚠️  Error processing conversation change: {e}")

    def _monitor_claude_processes(self):
        """Monitor for Claude CLI processes"""
        while self.is_monitoring:
            try:
                current_processes = {}
                
                # Find all claude processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        if proc.info['name'] == 'claude' or 'claude' in ' '.join(proc.info['cmdline'] or []):
                            pid = proc.info['pid']
                            current_processes[pid] = {
                                'process': proc,
                                'start_time': proc.info['create_time'],
                                'cmdline': proc.info['cmdline']
                            }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Detect new processes
                new_pids = set(current_processes.keys()) - set(self.claude_processes.keys())
                for pid in new_pids:
                    print(f"🔍 New Claude process detected: PID {pid}")
                    self._capture_session_start(pid, current_processes[pid])
                
                # Detect terminated processes
                dead_pids = set(self.claude_processes.keys()) - set(current_processes.keys())
                for pid in dead_pids:
                    print(f"💀 Claude process terminated: PID {pid}")
                    self._capture_session_end(pid)
                
                self.claude_processes = current_processes
                
            except Exception as e:
                print(f"⚠️  Process monitoring error: {e}")
            
            time.sleep(2)

    def _auto_save_loop(self):
        """Automatic capture loop"""
        while self.is_monitoring:
            time.sleep(self.auto_save_interval)
            if self.claude_processes:
                self._capture_current_state("auto_save")

    def _start_mcp_monitoring(self):
        """Monitor MCP logs for real-time changes"""
        if not self.claude_cache.exists():
            print("⚠️  Claude cache directory not found")
            return
            
        try:
            class MCPLogHandler(FileSystemEventHandler):
                def __init__(self, monitor):
                    self.monitor = monitor
                    
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith('.txt'):
                        self.monitor._on_mcp_log_change(event.src_path)
            
            self.mcp_observer = Observer()
            self.mcp_observer.schedule(
                MCPLogHandler(self),
                str(self.claude_cache),
                recursive=True
            )
            self.mcp_observer.start()
            print("👁️  MCP log monitoring started")
            
        except Exception as e:
            print(f"⚠️  MCP monitoring setup failed: {e}")

    def _on_mcp_log_change(self, log_path):
        """Handle MCP log changes"""
        try:
            with open(log_path, 'r') as f:
                content = f.read()
                if any(indicator in content.lower() for indicator in [
                    'rate limit', 'too many requests', '429', 'quota exceeded'
                ]):
                    print(f"🚨 RATE LIMIT DETECTED in {log_path}")
                    self._emergency_capture("rate_limit_detected")
        except Exception as e:
            pass

    def _capture_conversation_history(self):
        """Capture current conversation history"""
        conversations = {}
        
        if not self.claude_projects.exists():
            return conversations
            
        try:
            # Find all conversation files
            for jsonl_file in self.claude_projects.glob("**/*.jsonl"):
                try:
                    conversation_data = []
                    with open(jsonl_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                conversation_data.append(json.loads(line))
                    
                    if conversation_data:
                        conversations[str(jsonl_file.relative_to(self.claude_projects))] = {
                            "file_path": str(jsonl_file),
                            "last_modified": jsonl_file.stat().st_mtime,
                            "message_count": len(conversation_data),
                            "conversation": conversation_data[-50:]  # Last 50 messages
                        }
                        
                except Exception as e:
                    conversations[str(jsonl_file)] = {"error": str(e)}
                    
        except Exception as e:
            conversations["error"] = str(e)
            
        return conversations

    def _create_restoration_prompt(self, capture_data):
        """Create a restoration prompt for new Claude sessions"""
        conversations = capture_data.get('conversations', {})
        
        if not conversations:
            return "No previous conversation history available."
        
        # Find the most recent/relevant conversation
        latest_conversation = None
        latest_time = 0
        
        for conv_file, conv_data in conversations.items():
            if isinstance(conv_data, dict) and 'last_modified' in conv_data:
                if conv_data['last_modified'] > latest_time:
                    latest_time = conv_data['last_modified']
                    latest_conversation = conv_data
        
        if not latest_conversation or 'conversation' not in latest_conversation:
            return "No valid conversation history found."
        
        # Create restoration prompt
        restoration_prompt = f"""# Session Restoration Context

## Previous Session Summary
- **Session ID:** {capture_data.get('session_id', 'unknown')}
- **Project:** {capture_data.get('working_directory', 'unknown')}
- **Last Activity:** {capture_data.get('timestamp', 'unknown')}
- **Messages:** {latest_conversation.get('message_count', 0)} total

## Recent Conversation Context
Here's what we were working on:

"""
        
        # Add last few messages for context
        conversation = latest_conversation.get('conversation', [])
        for i, msg in enumerate(conversation[-10:]):  # Last 10 messages
            if msg.get('role') == 'user':
                restoration_prompt += f"**You:** {msg.get('content', '')[:200]}...\n\n"
            elif msg.get('role') == 'assistant':
                restoration_prompt += f"**Claude:** {msg.get('content', '')[:200]}...\n\n"
        
        restoration_prompt += f"""

## Current State
- **Git Status:** {capture_data.get('git_status', 'unknown')}
- **Recent Files:** {', '.join(capture_data.get('recent_files', [])[:10])}

## Restoration Instructions
Please acknowledge that you understand the context and are ready to continue where we left off.
"""
        
        return restoration_prompt

    def _capture_session_start(self, pid, process_info):
        """Capture when Claude session starts"""
        timestamp = datetime.now().isoformat()
        
        capture_data = {
            "event": "session_start",
            "timestamp": timestamp,
            "pid": pid,
            "cmdline": process_info['cmdline'],
            "working_directory": str(self.project_dir),
            "environment": dict(os.environ),
            "git_status": self._get_git_status(),
            "conversations": self._capture_conversation_history()
        }
        
        self._save_capture(capture_data, f"session_start_{pid}")
        print(f"📝 Session start captured: PID {pid}")

    def _capture_session_end(self, pid):
        """Capture when Claude session ends"""
        self._capture_current_state(f"session_end_{pid}")
        print(f"📝 Session end captured: PID {pid}")

    def _capture_current_state(self, event_type="auto_save"):
        """Capture current state of everything"""
        timestamp = datetime.now().isoformat()
        
        capture_data = {
            "event": event_type,
            "timestamp": timestamp,
            "session_id": self.session_id,
            "working_directory": str(self.project_dir),
            "git_status": self._get_git_status(),
            "recent_files": self._get_recent_files(),
            "claude_processes": list(self.claude_processes.keys()),
            "mcp_logs": self._capture_mcp_logs(),
            "conversations": self._capture_conversation_history(),
            "terminal_history": self._get_terminal_history(),
            "time_since_last_capture": (datetime.now() - self.last_capture_time).total_seconds()
        }
        
        self._save_capture(capture_data, event_type)
        self.last_capture_time = datetime.now()
        
        if event_type == "auto_save":
            conv_count = len(capture_data.get('conversations', {}))
            print(f"💾 Auto-save completed ({len(self.claude_processes)} processes, {conv_count} conversations)")

    def _emergency_capture(self, reason="emergency"):
        """Emergency capture for crashes/rate limits"""
        print(f"🚨 EMERGENCY CAPTURE: {reason}")
        self._capture_current_state(f"emergency_{reason}")
        print("✅ Emergency capture completed")

    def _emergency_save(self, signum, frame):
        """Signal handler for emergency saves"""
        print(f"\n🚨 Received signal {signum} - Emergency save...")
        self._emergency_capture("signal_handler")
        self.stop_monitoring()
        sys.exit(0)

    def _capture_mcp_logs(self):
        """Capture latest MCP logs"""
        logs = {}
        
        if not self.claude_cache.exists():
            return logs
            
        try:
            for log_dir in self.claude_cache.iterdir():
                if log_dir.is_dir() and 'mcp-logs' in log_dir.name:
                    log_files = list(log_dir.glob("*.txt"))
                    if log_files:
                        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                        try:
                            with open(latest_log, 'r') as f:
                                logs[log_dir.name] = {
                                    "file": str(latest_log),
                                    "modified": latest_log.stat().st_mtime,
                                    "size": latest_log.stat().st_size,
                                    "content_preview": f.read()[:1000]
                                }
                        except Exception as e:
                            logs[log_dir.name] = {"error": str(e)}
        except Exception as e:
            logs["error"] = str(e)
            
        return logs

    def _get_git_status(self):
        """Get git status"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            return result.stdout
        except:
            return "Not a git repository"

    def _get_recent_files(self):
        """Get recently modified files"""
        try:
            result = subprocess.run(
                ['find', '.', '-type', 'f', '-mtime', '-1'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            return result.stdout.strip().split('\n')[:50]
        except:
            return []

    def _get_terminal_history(self):
        """Get recent terminal history"""
        try:
            result = subprocess.run(
                ['tail', '-n', '50', os.path.expanduser('~/.bash_history')],
                capture_output=True,
                text=True
            )
            return result.stdout.strip().split('\n')
        except:
            return []

    def _save_capture(self, capture_data, event_type):
        """Save capture data to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.session_id}_{event_type}_{timestamp}.json"
        filepath = self.archive_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(capture_data, f, indent=2)
            
            # Create human-readable summary
            self._create_readable_summary(capture_data, filepath)
            
            # Create restoration prompt
            restoration_prompt = self._create_restoration_prompt(capture_data)
            restore_file = filepath.with_suffix('.restore.md')
            with open(restore_file, 'w') as f:
                f.write(restoration_prompt)
            
        except Exception as e:
            print(f"⚠️  Failed to save capture: {e}")

    def _create_readable_summary(self, capture_data, json_file):
        """Create markdown summary"""
        md_file = json_file.with_suffix('.md')
        
        conversations = capture_data.get('conversations', {})
        conv_summary = f"{len(conversations)} conversations captured"
        
        content = f"""# Enhanced Claude Auto-Monitor Capture
        
## Event: {capture_data.get('event', 'unknown')}
**Timestamp:** {capture_data.get('timestamp', 'unknown')}
**Session ID:** {capture_data.get('session_id', 'unknown')}

## System State
- **Working Directory:** {capture_data.get('working_directory', 'unknown')}
- **Active Claude Processes:** {len(capture_data.get('claude_processes', []))}
- **Conversation History:** {conv_summary}
- **Time Since Last Capture:** {capture_data.get('time_since_last_capture', 'unknown')}s

## Git Status
```
{capture_data.get('git_status', 'No git status')}
```

## Recent Files
{chr(10).join(f"- {f}" for f in capture_data.get('recent_files', [])[:20])}

## Conversation Files
{chr(10).join(f"- {name}: {data.get('message_count', 0)} messages" for name, data in conversations.items() if isinstance(data, dict))}

## Recovery Commands
```bash
# Navigate to project
cd {capture_data.get('working_directory', 'unknown')}

# View restoration prompt
cat {json_file.with_suffix('.restore.md').name}

# Start new Claude session with context
claude
# Then paste the restoration prompt content

# Continue monitoring
python claude-auto-monitor.py --restore {capture_data.get('session_id', 'unknown')}
```
"""
        
        try:
            with open(md_file, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"⚠️  Failed to create summary: {e}")

    def compress_session(self, session_id=None, keep_last_n=10):
        """Compress old captures into a single session summary"""
        target_session = session_id or self.session_id
        
        print(f"🗜️  Compressing session: {target_session}")
        
        # Find all captures for this session
        captures = sorted(self.archive_dir.glob(f"{target_session}_*.json"))
        
        if len(captures) <= keep_last_n:
            print(f"⚠️  Only {len(captures)} captures found, no compression needed")
            return
        
        # Separate captures to keep vs compress
        to_compress = captures[:-keep_last_n]
        to_keep = captures[-keep_last_n:]
        
        print(f"📦 Compressing {len(to_compress)} captures, keeping {len(to_keep)} recent")
        
        # Create compressed session summary
        compressed_data = self._create_compressed_summary(to_compress)
        
        # Save compressed summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        compressed_file = self.archive_dir / f"{target_session}_COMPRESSED_{timestamp}.json"
        
        try:
            with open(compressed_file, 'w') as f:
                json.dump(compressed_data, f, indent=2)
            
            # Create compressed restoration prompt
            self._create_compressed_restoration_prompt(compressed_data, compressed_file)
            
            # Archive old files
            archive_dir = self.archive_dir / "compressed_archives"
            archive_dir.mkdir(exist_ok=True)
            
            for capture in to_compress:
                # Move old files to archive
                archived_file = archive_dir / capture.name
                capture.rename(archived_file)
                
                # Also move associated files
                for suffix in ['.md', '.restore.md']:
                    old_file = capture.with_suffix(suffix)
                    if old_file.exists():
                        old_file.rename(archive_dir / old_file.name)
            
            print(f"✅ Compression complete: {compressed_file.name}")
            print(f"📁 Archived {len(to_compress)} files to compressed_archives/")
            
        except Exception as e:
            print(f"❌ Compression failed: {e}")

    def _create_compressed_summary(self, capture_files):
        """Create intelligent summary from multiple captures"""
        all_data = []
        
        # Load all capture data
        for capture_file in capture_files:
            try:
                with open(capture_file, 'r') as f:
                    data = json.load(f)
                    all_data.append(data)
            except Exception as e:
                print(f"⚠️  Failed to load {capture_file}: {e}")
        
        if not all_data:
            return {"error": "No data to compress"}
        
        # Extract key patterns
        first_capture = all_data[0]
        last_capture = all_data[-1]
        
        # Find unique conversations across all captures
        all_conversations = {}
        for data in all_data:
            convs = data.get('conversations', {})
            for conv_name, conv_data in convs.items():
                if isinstance(conv_data, dict) and 'conversation' in conv_data:
                    if conv_name not in all_conversations:
                        all_conversations[conv_name] = []
                    all_conversations[conv_name].extend(conv_data['conversation'])
        
        # Deduplicate conversations by message content
        for conv_name in all_conversations:
            unique_messages = []
            seen_contents = set()
            
            for msg in all_conversations[conv_name]:
                content_hash = hashlib.md5(str(msg.get('content', '')).encode()).hexdigest()
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    unique_messages.append(msg)
            
            # Keep only the most recent messages
            all_conversations[conv_name] = unique_messages[-100:]  # Last 100 unique messages
        
        # Aggregate file changes
        all_files = set()
        for data in all_data:
            all_files.update(data.get('recent_files', []))
        
        # Create compressed summary
        compressed_data = {
            "event": "compressed_session_summary",
            "timestamp": datetime.now().isoformat(),
            "session_id": first_capture.get('session_id'),
            "compression_period": {
                "start": first_capture.get('timestamp'),
                "end": last_capture.get('timestamp'),
                "capture_count": len(all_data)
            },
            "working_directory": first_capture.get('working_directory'),
            "final_git_status": last_capture.get('git_status'),
            "all_modified_files": sorted(list(all_files)),
            "conversations_summary": {
                name: {
                    "message_count": len(messages),
                    "conversation": messages  # All unique messages
                }
                for name, messages in all_conversations.items()
            },
            "process_activity": {
                "total_processes_seen": len(set(
                    pid for data in all_data 
                    for pid in data.get('claude_processes', [])
                )),
                "rate_limit_events": len([
                    data for data in all_data 
                    if 'rate_limit' in data.get('event', '')
                ]),
                "crash_events": len([
                    data for data in all_data 
                    if 'session_end' in data.get('event', '')
                ])
            },
            "key_events": [
                {
                    "timestamp": data.get('timestamp'),
                    "event": data.get('event'),
                    "significance": self._rate_event_significance(data)
                }
                for data in all_data
                if self._is_significant_event(data)
            ]
        }
        
        return compressed_data

    def _rate_event_significance(self, data):
        """Rate how significant an event is for compression"""
        event = data.get('event', '')
        
        if 'emergency' in event or 'rate_limit' in event:
            return 10  # Critical
        elif 'session_start' in event or 'session_end' in event:
            return 8   # High
        elif 'conversation_update' in event:
            return 6   # Medium
        else:
            return 3   # Low

    def _is_significant_event(self, data):
        """Determine if an event should be kept in compressed summary"""
        return self._rate_event_significance(data) >= 6

    def _create_compressed_restoration_prompt(self, compressed_data, compressed_file):
        """Create restoration prompt from compressed data"""
        conversations = compressed_data.get('conversations_summary', {})
        
        restoration_prompt = f"""# Compressed Session Restoration Context

## Session Summary
- **Session ID:** {compressed_data.get('session_id', 'unknown')}
- **Project:** {compressed_data.get('working_directory', 'unknown')}
- **Period:** {compressed_data.get('compression_period', {}).get('start', 'unknown')} to {compressed_data.get('compression_period', {}).get('end', 'unknown')}
- **Total Captures:** {compressed_data.get('compression_period', {}).get('capture_count', 0)}

## Activity Summary
- **Processes:** {compressed_data.get('process_activity', {}).get('total_processes_seen', 0)} Claude instances
- **Rate Limits:** {compressed_data.get('process_activity', {}).get('rate_limit_events', 0)} events
- **Crashes:** {compressed_data.get('process_activity', {}).get('crash_events', 0)} events
- **Files Modified:** {len(compressed_data.get('all_modified_files', []))} files

## Key Conversation Threads
"""
        
        # Add conversation summaries
        for conv_name, conv_data in conversations.items():
            if isinstance(conv_data, dict) and 'conversation' in conv_data:
                messages = conv_data['conversation']
                restoration_prompt += f"""
### {conv_name}
- **Total Messages:** {len(messages)}
- **Recent Context:**
"""
                
                # Add last few messages for context
                for msg in messages[-5:]:  # Last 5 messages
                    if msg.get('role') == 'user':
                        restoration_prompt += f"  **You:** {msg.get('content', '')[:150]}...\n"
                    elif msg.get('role') == 'assistant':
                        restoration_prompt += f"  **Claude:** {msg.get('content', '')[:150]}...\n"
        
        restoration_prompt += f"""

## Project State
- **Git Status:** {compressed_data.get('final_git_status', 'unknown')}
- **Key Files:** {', '.join(compressed_data.get('all_modified_files', [])[:15])}

## Restoration Instructions
This is a compressed summary of {compressed_data.get('compression_period', {}).get('capture_count', 0)} captured sessions.
Please acknowledge that you understand this compressed context and are ready to continue the work.

**Note:** For more detailed history, see the full compressed data in {compressed_file.name}
"""
        
        restore_file = compressed_file.with_suffix('.restore.md')
        try:
            with open(restore_file, 'w') as f:
                f.write(restoration_prompt)
        except Exception as e:
            print(f"⚠️  Failed to create compressed restoration prompt: {e}")

    def stop_monitoring(self):
        """Stop all monitoring"""
        print("🛑 Stopping enhanced auto-monitoring...")
        self.is_monitoring = False
        
        if self.mcp_observer:
            self.mcp_observer.stop()
            self.mcp_observer.join()
            
        if self.chat_observer:
            self.chat_observer.stop()
            self.chat_observer.join()
        
        self._capture_current_state("monitor_stop")
        print("✅ Enhanced auto-monitoring stopped")

    def list_captures(self):
        """List all captures for this session"""
        captures = sorted(self.archive_dir.glob(f"{self.session_id}_*.json"))
        
        print(f"📋 Found {len(captures)} captures for session {self.session_id}:")
        for capture in captures:
            print(f"  • {capture.name}")
            restore_file = capture.with_suffix('.restore.md')
            if restore_file.exists():
                print(f"    📄 Restoration prompt: {restore_file.name}")
        
        return captures

    def restore_from_capture(self, capture_file):
        """Load and display capture data"""
        try:
            with open(capture_file, 'r') as f:
                data = json.load(f)
            
            conversations = data.get('conversations', {})
            
            print(f"🔄 Capture: {data.get('event', 'unknown')}")
            print(f"📅 Time: {data.get('timestamp', 'unknown')}")
            print(f"📁 Directory: {data.get('working_directory', 'unknown')}")
            print(f"🤖 Active processes: {len(data.get('claude_processes', []))}")
            print(f"💬 Conversations: {len(conversations)}")
            
            # Show restoration prompt
            restore_file = Path(capture_file).with_suffix('.restore.md')
            if restore_file.exists():
                print(f"\n📄 Restoration prompt available: {restore_file.name}")
                print("💡 Copy this content to your new Claude session:")
                print("-" * 50)
                with open(restore_file, 'r') as f:
                    print(f.read())
            
            return data
        except Exception as e:
            print(f"❌ Failed to restore: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Enhanced Claude Auto-Monitor System")
    parser.add_argument('--project-dir', default=None, help='Project directory to monitor')
    parser.add_argument('--interval', type=int, default=30, help='Auto-save interval in seconds')
    parser.add_argument('--list', action='store_true', help='List captures and exit')
    parser.add_argument('--restore', help='Show specific capture data')
    parser.add_argument('--compress', help='Compress session captures (session_id or "auto")')
    parser.add_argument('--keep-recent', type=int, default=10, help='Keep N recent captures when compressing')
    
    args = parser.parse_args()
    
    monitor = ClaudeAutoMonitor(
        project_dir=args.project_dir,
        auto_save_interval=args.interval
    )
    
    if args.list:
        monitor.list_captures()
        return
    
    if args.restore:
        capture_file = monitor.archive_dir / f"{args.restore}.json"
        if capture_file.exists():
            monitor.restore_from_capture(capture_file)
        else:
            print(f"❌ Capture not found: {capture_file}")
            # Try to find partial matches
            matches = list(monitor.archive_dir.glob(f"*{args.restore}*.json"))
            if matches:
                print(f"🔍 Found {len(matches)} partial matches:")
                for match in matches:
                    print(f"  • {match.name}")
        return
    
    if args.compress:
        if args.compress == "auto":
            # Auto-compress all sessions with >20 captures
            all_sessions = {}
            for capture in monitor.archive_dir.glob("*_*.json"):
                if "COMPRESSED" not in capture.name:
                    session_id = capture.name.split('_')[0] + '_' + capture.name.split('_')[1]
                    all_sessions[session_id] = all_sessions.get(session_id, 0) + 1
            
            for session_id, count in all_sessions.items():
                if count > 20:
                    print(f"🗜️  Auto-compressing session {session_id} ({count} captures)")
                    monitor.compress_session(session_id, args.keep_recent)
        else:
            monitor.compress_session(args.compress, args.keep_recent)
        return
    
    try:
        monitor.start_monitoring()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()