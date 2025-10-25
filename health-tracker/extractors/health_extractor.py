"""
Claude健康数据提取器

使用Claude AI从文本和图片中提取结构化健康数据
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from anthropic import Anthropic


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

        if use_openrouter:
            # 使用 OpenRouter
            self.client = Anthropic(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
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
            self.client = Anthropic(api_key=api_key)
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
            # 调用Claude API
            response = self.client.messages.create(
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
   - weight_feeling: 对体重的主观感受（如"感觉轻了"、"有点重"等）

2. **睡眠相关**:
   - sleep_duration: 总睡眠时长(小时)
   - sleep_start: 入睡时间
   - sleep_end: 起床时间
   - sleep_quality: 睡眠质量（可以是主观评分1-10，或描述如"好"、"一般"、"差"）
   - deep_sleep_duration: 深睡眠时长(小时)
   - sleep_notes: 睡眠相关的备注

3. **运动相关**:
   - exercises: 运动列表，每项包含:
     - type: 运动类型（如跑步、游泳、健身等）
     - duration: 时长(分钟)
     - distance: 距离(km，如适用)
     - intensity: 强度（轻度、中度、高强度）
     - calories: 消耗卡路里
     - feeling: 运动后感受

4. **饮食相关**:
   - meals: 餐食列表，每项包含:
     - meal_type: 餐次（早餐、午餐、晚餐、加餐）
     - description: 食物描述
     - calories: 估算卡路里
     - notes: 备注

5. **其他健康指标**:
   - heart_rate: 心率(bpm)
   - blood_pressure: 血压（如"120/80"）
   - mood: 心情（1-10分或描述）
   - energy_level: 精力水平（1-10分或描述）
   - water_intake: 饮水量(ml)
   - steps: 步数

6. **主观感受和目标**:
   - overall_feeling: 整体感受
   - health_notes: 其他健康相关备注
   - goals: 提到的健康目标

**重要指示**:
- 只提取笔记中明确提到的信息，不要编造数据
- 如果某个字段没有提到，不要包含在JSON中
- 对于模糊的描述（如"7小时左右"），提取具体数值7并在notes中标注"约"
- 理解自然语言表达，如"今天68.5公斤"应提取为weight: 68.5
- 理解情感和主观描述，如"感觉很累但很爽"
- 如果图片中包含数据（如体重秤截图、健身APP截图），请识别并提取
- 返回格式必须是有效的JSON

请直接返回JSON，不要包含任何其他文字说明。
"""

    def _encode_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        编码图片为base64

        Args:
            image_path: 图片路径

        Returns:
            Claude API所需的图片内容格式
        """
        try:
            path = Path(image_path)
            if not path.exists():
                print(f"Image not found: {image_path}")
                return None

            with open(path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # 判断图片类型
            suffix = path.suffix.lower()
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
            response = self.client.messages.create(
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

            # 体重数据
            if 'weight' in entry:
                lines.append(f"  体重: {entry['weight']}kg")
            if 'body_fat_percentage' in entry:
                lines.append(f"  体脂率: {entry['body_fat_percentage']}%")

            # 睡眠数据
            if 'sleep_duration' in entry:
                lines.append(f"  睡眠: {entry['sleep_duration']}小时")
            if 'sleep_quality' in entry:
                lines.append(f"  睡眠质量: {entry['sleep_quality']}")

            # 运动数据
            if 'exercises' in entry and entry['exercises']:
                lines.append(f"  运动:")
                for ex in entry['exercises']:
                    ex_type = ex.get('type', '未知')
                    duration = ex.get('duration', '?')
                    lines.append(f"    - {ex_type} {duration}分钟")

            # 主观感受
            if 'overall_feeling' in entry:
                lines.append(f"  整体感受: {entry['overall_feeling']}")

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
            response = self.client.messages.create(
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
