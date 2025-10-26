"""
Claude健康数据提取器

使用Claude AI从文本和图片中提取结构化健康数据
"""

import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class HealthDataExtractor:
    """使用Claude提取健康数据"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        use_openrouter: bool = False
    ):
        """
        初始化提取器

        Args:
            api_key: API密钥（Anthropic 或 OpenRouter）
            model: 使用的模型名称
            use_openrouter: 是否使用 OpenRouter
        """
        self.use_openrouter = use_openrouter
        self.model = model
        self.anthropic_client = None
        self.openai_client = None

        if use_openrouter:
            # OpenRouter 使用 OpenAI 兼容的 API
            if not OPENAI_AVAILABLE:
                raise ImportError("使用 OpenRouter 需要安装 openai 包: pip install openai")

            # 使用 OpenAI SDK 调用 OpenRouter
            self.openai_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/health-tracker",
                    "X-Title": "Health Tracker"
                }
            )

            # OpenRouter 使用不同的模型名称格式
            # 如果模型名不包含提供商前缀，自动添加
            if not model.startswith("anthropic/"):
                # 转换标准 Anthropic 模型名到 OpenRouter 格式
                model_map = {
                    "claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet",
                    "claude-3-opus-20240229": "anthropic/claude-3-opus",
                    "claude-3-haiku-20240307": "anthropic/claude-3-haiku",
                }
                self.model = model_map.get(model, f"anthropic/{model}")
            print(f"Using OpenRouter with model: {self.model}")
        else:
            # 使用原生 Anthropic API
            self.anthropic_client = Anthropic(api_key=api_key)
            print(f"Using Anthropic API with model: {self.model}")

    def extract_from_note(
        self,
        text: str,
        images: Optional[List[str]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从笔记中提取健康数据

        Args:
            text: 笔记文本内容
            images: 图片路径列表
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            结构化的健康数据
        """
        if self.use_openrouter:
            return self._extract_with_openrouter(text, images, date)
        else:
            return self._extract_with_anthropic(text, images, date)

    def _extract_with_anthropic(
        self,
        text: str,
        images: Optional[List[str]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 Anthropic API 提取数据"""
        # 构建提示词
        prompt = self._build_extraction_prompt(text, date)

        # 构建消息内容
        content = [{"type": "text", "text": prompt}]

        # 添加图片
        if images:
            for image_path in images:
                image_content = self._encode_image(image_path)
                if image_content:
                    content.append(image_content)

        try:
            # 调用Anthropic API
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # 解析响应
            result_text = response.content[0].text
            extracted_data = self._parse_claude_response(result_text)

            # 添加元数据
            extracted_data['raw_text'] = text
            extracted_data['processed_date'] = date
            extracted_data['has_images'] = bool(images)
            extracted_data['image_count'] = len(images) if images else 0

            return extracted_data

        except Exception as e:
            print(f"Error extracting data: {e}")
            return {
                'error': str(e),
                'raw_text': text,
                'processed_date': date
            }

    def _extract_with_openrouter(
        self,
        text: str,
        images: Optional[List[str]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 OpenRouter (OpenAI 格式) 提取数据"""
        # 构建提示词
        prompt = self._build_extraction_prompt(text, date)

        # OpenAI 格式的消息内容
        content_parts = [{"type": "text", "text": prompt}]

        # 添加图片 (OpenAI 格式)
        if images:
            for image_path in images:
                image_content = self._encode_image_for_openai(image_path)
                if image_content:
                    content_parts.append(image_content)

        try:
            # 调用 OpenRouter (OpenAI SDK)
            response = self.openai_client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": content_parts if len(content_parts) > 1 else prompt
                }]
            )

            # 解析响应
            result_text = response.choices[0].message.content
            extracted_data = self._parse_claude_response(result_text)

            # 添加元数据
            extracted_data['raw_text'] = text
            extracted_data['processed_date'] = date
            extracted_data['has_images'] = bool(images)
            extracted_data['image_count'] = len(images) if images else 0

            return extracted_data

        except Exception as e:
            print(f"Error extracting data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'raw_text': text,
                'processed_date': date
            }

    def _build_extraction_prompt(self, text: str, date: Optional[str] = None) -> str:
        """构建提取数据的提示词"""
        date_info = f"日期: {date}\n" if date else ""

        return f"""你是一个专业的健康数据提取助手。请从以下笔记中提取所有健康相关数据，并以JSON格式返回。

{date_info}
笔记内容:
{text}

请提取以下信息（如果笔记中有提到的话）:

1. **体重相关**:
   - weight: 体重(kg)
   - body_fat_percentage: 体脂率(%)
   - muscle_mass: 肌肉量(kg)
   - bmi: BMI指数
   - basal_metabolism: 基础代谢(kcal/天)
   - visceral_fat_level: 内脏脂肪等级
   - weight_feeling: 对体重的主观感受

2. **睡眠相关**:
   - sleep_duration: 总睡眠时长(小时)
   - sleep_start: 入睡时间
   - sleep_end: 起床时间
   - sleep_quality: 睡眠质量（1-10分或描述）
   - deep_sleep_duration: 深睡眠时长(小时)
   - rem_sleep_duration: REM睡眠时长(小时)
   - sleep_notes: 睡眠相关备注
   - urination_count: 夜间排尿次数

3. **心血管相关**:
   - heart_rate: 心率(bpm)
   - resting_heart_rate: 静息心率(bpm)
   - hrv: 心率变异性(HRV)
   - blood_pressure: 血压（如"120/80"）
   - vo2_max: 最大摄氧量(VO2 Max)

4. **运动相关**:
   - exercises: 运动列表，每项包含:
     - type: 运动类型
     - duration: 时长(分钟)
     - distance: 距离(km)
     - intensity: 强度
     - calories: 消耗卡路里
     - feeling: 运动后感受

5. **饮食相关**:
   - meals: 餐食列表，每项包含:
     - meal_type: 餐次
     - description: 食物描述
     - calories: 估算卡路里
     - notes: 备注

6. **疼痛和症状**:
   - pain_score: 疼痛评分(1-10)
   - pain_location: 疼痛部位
   - morning_stiffness_duration: 晨僵持续时间(分钟)
   - symptoms: 其他症状描述

7. **主观感受**:
   - mood: 心情（1-10分或描述）
   - energy_level: 精力水平（1-10分或描述）
   - overall_feeling: 整体感受

8. **其他指标**:
   - water_intake: 饮水量(ml)
   - steps: 步数
   - health_notes: 其他健康备注
   - goals: 健康目标

**重要指示**:
- 只提取笔记中明确提到的信息，不要编造数据
- 如果某个字段没有提到，不要包含在JSON中
- 对于模糊的描述（如"7小时左右"），提取具体数值7并在notes中标注"约"
- 理解自然语言表达，如"今天68.5公斤"应提取为weight: 68.5
- 理解情感和主观描述，如"感觉很累但很爽"
- 如果图片中包含数据（如体重秤截图、健身APP截图），请识别并提取
- **JSON 必须是扁平结构，不要使用嵌套对象**
- **所有字段都在顶层，不要分组到子对象中**

**字段名要求（必须完全一致）**:
- 内脏脂肪：visceral_fat_level（不是 visceral_fat）
- 排尿次数：urination_count（不是 night_urination_count）
- 静息心率：resting_heart_rate（不是 heart_rate，heart_rate 用于运动时心率）
- 疼痛评分：pain_score（单独字段，不要放在 health_notes 里）
- 疼痛部位：pain_location（单独字段）
- 晨僵时间：morning_stiffness_duration（单独字段，单位：分钟）
- 症状描述：symptoms（单独字段，如"筋膜炎"、"跟腱疼痛"）

**JSON 格式示例**（扁平结构，字段名必须完全一致）:
```json
{{
  "weight": 87.1,
  "muscle_mass": 36.9,
  "basal_metabolism": 1788,
  "visceral_fat_level": 9,
  "sleep_duration": 8.6,
  "deep_sleep_duration": 1.85,
  "rem_sleep_duration": 2.47,
  "resting_heart_rate": 49,
  "hrv": 53,
  "urination_count": 1,
  "mood": "平复",
  "pain_score": 2,
  "pain_location": "跟腱止点",
  "morning_stiffness_duration": 1,
  "symptoms": "筋膜炎、跟腱疼痛"
}}
```

**错误示例**（不要这样做）:
```json
{{
  "body_metrics": {{
    "weight": 68.5
  }},
  "sleep": {{
    "sleep_duration": 7.5
  }}
}}
```

请直接返回扁平的JSON，不要包含任何其他文字说明。
"""

    def _encode_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        编码图片为base64（支持本地文件和远程URL）

        Args:
            image_path: 图片路径或URL

        Returns:
            Claude API所需的图片内容格式
        """
        try:
            # 检测是否为远程URL
            if image_path.startswith(('http://', 'https://')):
                print(f"Downloading remote image: {image_path}")
                response = requests.get(image_path, timeout=30)
                response.raise_for_status()
                image_bytes = response.content

                # 从URL获取文件扩展名
                from urllib.parse import urlparse, unquote
                parsed_url = urlparse(image_path)
                url_path = unquote(parsed_url.path)
                suffix = Path(url_path).suffix.lower()

                # 如果URL没有扩展名，尝试从Content-Type获取
                if not suffix:
                    content_type = response.headers.get('Content-Type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        suffix = '.jpg'
                    elif 'png' in content_type:
                        suffix = '.png'
                    elif 'webp' in content_type:
                        suffix = '.webp'
                    elif 'gif' in content_type:
                        suffix = '.gif'
                    else:
                        suffix = '.jpg'  # 默认

                print(f"✓ Downloaded {len(image_bytes)} bytes, type: {suffix}")
            else:
                # 本地文件路径
                path = Path(image_path)
                if not path.exists():
                    print(f"Image not found: {image_path}")
                    return None

                with open(path, 'rb') as f:
                    image_bytes = f.read()

                suffix = path.suffix.lower()

            # 编码为base64
            image_data = base64.standard_b64encode(image_bytes).decode('utf-8')

            # 判断图片类型
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(suffix, 'image/jpeg')

            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            }

        except requests.RequestException as e:
            print(f"Error downloading remote image {image_path}: {e}")
            return None
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None

    def _encode_image_for_openai(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        编码图片为 OpenAI Vision API 格式（支持本地文件和远程URL）

        Args:
            image_path: 图片路径或URL

        Returns:
            OpenAI API所需的图片内容格式
        """
        try:
            # 检测是否为远程URL
            if image_path.startswith(('http://', 'https://')):
                print(f"Downloading remote image: {image_path}")
                response = requests.get(image_path, timeout=30)
                response.raise_for_status()
                image_bytes = response.content

                # 从URL获取文件扩展名
                from urllib.parse import urlparse, unquote
                parsed_url = urlparse(image_path)
                url_path = unquote(parsed_url.path)
                suffix = Path(url_path).suffix.lower()

                # 如果URL没有扩展名，尝试从Content-Type获取
                if not suffix:
                    content_type = response.headers.get('Content-Type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        suffix = '.jpg'
                    elif 'png' in content_type:
                        suffix = '.png'
                    elif 'webp' in content_type:
                        suffix = '.webp'
                    elif 'gif' in content_type:
                        suffix = '.gif'
                    else:
                        suffix = '.jpg'  # 默认

                print(f"✓ Downloaded {len(image_bytes)} bytes, type: {suffix}")
            else:
                # 本地文件路径
                path = Path(image_path)
                if not path.exists():
                    print(f"Image not found: {image_path}")
                    return None

                with open(path, 'rb') as f:
                    image_bytes = f.read()

                suffix = path.suffix.lower()

            # 编码为base64
            image_data = base64.standard_b64encode(image_bytes).decode('utf-8')

            # 判断图片类型
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(suffix, 'image/jpeg')

            # OpenAI Vision API 格式
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_data}"
                }
            }

        except requests.RequestException as e:
            print(f"Error downloading remote image {image_path}: {e}")
            return None
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析Claude的响应

        Args:
            response_text: Claude返回的文本

        Returns:
            解析后的字典
        """
        try:
            # 尝试提取JSON（可能被markdown代码块包裹）
            json_str = response_text.strip()

            # 移除可能的markdown代码块标记
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            elif json_str.startswith('```'):
                json_str = json_str[3:]

            if json_str.endswith('```'):
                json_str = json_str[:-3]

            json_str = json_str.strip()

            # 解析JSON
            data = json.loads(json_str)
            return data

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response text: {response_text}")
            return {
                'parsing_error': str(e),
                'raw_response': response_text
            }

    def analyze_trends(
        self,
        historical_data: List[Dict[str, Any]],
        question: Optional[str] = None
    ) -> str:
        """
        使用Claude分析健康数据趋势

        Args:
            historical_data: 历史数据列表
            question: 用户的具体问题（可选）

        Returns:
            Claude的分析和建议
        """
        # 格式化历史数据
        data_summary = self._format_data_for_analysis(historical_data)

        # 构建分析提示
        if question:
            prompt = f"""作为健康顾问，请分析以下健康数据并回答用户的问题。

用户问题: {question}

历史数据:
{data_summary}

请提供:
1. 针对用户问题的具体回答
2. 相关数据趋势分析
3. 可能的原因解释
4. 个性化建议

请用友好、专业的语气回答。
"""
        else:
            prompt = f"""作为健康顾问，请分析以下健康数据并提供深度洞察。

历史数据:
{data_summary}

请分析:
1. 关键趋势和变化（体重、睡眠、运动等）
2. 各指标之间的相关性（如睡眠质量与运动的关系）
3. 值得注意的异常或模式
4. 可能的健康风险
5. 个性化的改进建议

请提供具体、可操作的建议，用友好的语气表达。
"""

        try:
            if self.use_openrouter:
                # 使用 OpenRouter (OpenAI SDK)
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content
            else:
                # 使用 Anthropic SDK
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text

        except Exception as e:
            return f"分析时出错: {str(e)}"

    def _format_data_for_analysis(self, data: List[Dict[str, Any]]) -> str:
        """格式化数据用于分析"""
        if not data:
            return "暂无数据"

        lines = []
        for entry in data:
            date = entry.get('processed_date', entry.get('date', '未知日期'))
            lines.append(f"\n日期: {date}")

            # 体重相关数据
            if 'weight' in entry:
                lines.append(f"  体重: {entry['weight']}kg")
            if 'body_fat_percentage' in entry:
                lines.append(f"  体脂率: {entry['body_fat_percentage']}%")
            if 'muscle_mass' in entry:
                lines.append(f"  肌肉量: {entry['muscle_mass']}kg")
            if 'basal_metabolism' in entry:
                lines.append(f"  基础代谢: {entry['basal_metabolism']}kcal/天")
            if 'visceral_fat_level' in entry:
                lines.append(f"  内脏脂肪等级: {entry['visceral_fat_level']}")
            if 'bmi' in entry:
                lines.append(f"  BMI: {entry['bmi']}")

            # 睡眠数据
            if 'sleep_duration' in entry:
                lines.append(f"  睡眠时长: {entry['sleep_duration']}小时")
            if 'deep_sleep_duration' in entry:
                lines.append(f"  深度睡眠: {entry['deep_sleep_duration']}小时")
            if 'rem_sleep_duration' in entry:
                lines.append(f"  REM睡眠: {entry['rem_sleep_duration']}小时")
            if 'sleep_quality' in entry:
                lines.append(f"  睡眠质量: {entry['sleep_quality']}")
            if 'urination_count' in entry:
                lines.append(f"  夜间排尿: {entry['urination_count']}次")

            # 心血管数据
            if 'resting_heart_rate' in entry:
                lines.append(f"  静息心率: {entry['resting_heart_rate']}bpm")
            if 'heart_rate' in entry:
                lines.append(f"  心率: {entry['heart_rate']}bpm")
            if 'hrv' in entry:
                lines.append(f"  HRV: {entry['hrv']}")
            if 'blood_pressure' in entry:
                lines.append(f"  血压: {entry['blood_pressure']}")
            if 'vo2_max' in entry:
                lines.append(f"  VO2 Max: {entry['vo2_max']}")

            # 疼痛和症状
            if 'pain_score' in entry:
                lines.append(f"  疼痛评分: {entry['pain_score']}/10")
            if 'pain_location' in entry:
                lines.append(f"  疼痛部位: {entry['pain_location']}")
            if 'morning_stiffness_duration' in entry:
                lines.append(f"  晨僵时间: {entry['morning_stiffness_duration']}分钟")
            if 'symptoms' in entry:
                lines.append(f"  症状: {entry['symptoms']}")

            # 主观感受
            if 'mood' in entry:
                lines.append(f"  心情: {entry['mood']}")
            if 'energy_level' in entry:
                lines.append(f"  精力水平: {entry['energy_level']}")
            if 'overall_feeling' in entry:
                lines.append(f"  整体感受: {entry['overall_feeling']}")

            # 运动数据
            if 'exercises' in entry and entry['exercises']:
                lines.append(f"  运动:")
                for ex in entry['exercises']:
                    ex_type = ex.get('type', '未知')
                    duration = ex.get('duration', '?')
                    lines.append(f"    - {ex_type} {duration}分钟")

            # 其他指标
            if 'steps' in entry:
                lines.append(f"  步数: {entry['steps']}")
            if 'water_intake' in entry:
                lines.append(f"  饮水量: {entry['water_intake']}ml")
            if 'health_notes' in entry:
                lines.append(f"  备注: {entry['health_notes']}")

        return '\n'.join(lines)

    def generate_visualization_code(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "趋势图"
    ) -> str:
        """
        让Claude生成数据可视化代码

        Args:
            data: 要可视化的数据
            chart_type: 图表类型描述

        Returns:
            Python代码字符串
        """
        data_summary = self._format_data_for_analysis(data)

        prompt = f"""请为以下健康数据生成Python matplotlib可视化代码。

数据:
{data_summary}

需求: {chart_type}

要求:
1. 使用matplotlib库
2. 代码要完整可执行
3. 图表要清晰美观
4. 支持中文显示
5. 包含适当的标题、标签和图例

请只返回Python代码，不要包含任何解释。
"""

        try:
            if self.use_openrouter:
                # 使用 OpenRouter (OpenAI SDK)
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                code = response.choices[0].message.content
            else:
                # 使用 Anthropic SDK
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                code = response.content[0].text

            # 提取代码块
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0]
            elif '```' in code:
                code = code.split('```')[1].split('```')[0]

            return code.strip()

        except Exception as e:
            return f"# 生成代码时出错: {str(e)}"
