"""
Demo data generator for testing the system without API credentials
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict


class DemoDataGenerator:
    """Generate realistic demo data for testing"""

    def __init__(self):
        self.xiaomi_topics = [
            "小米14 Ultra拍照效果惊艳",
            "小米汽车SU7交付量突破新高",
            "澎湃OS 2.0系统体验分享",
            "小米Civi 4 Pro颜值在线",
            "小米智能家居生态越来越完善了",
            "雷军直播带货创造新纪录",
            "小米MIX Fold 4折叠屏真香",
            "小米手环9使用一周体验",
            "小米电视性价比无敌",
            "小米路由器mesh组网教程",
            "小米14系列销量又破纪录",
            "澎湃芯片自研进展神速",
            "小米之家服务体验超好",
            "雷军年度演讲太感动了",
            "小米平板6 Max追剧神器",
        ]

        self.authors_xhs = [
            "数码小达人", "科技评测君", "米粉阿宝", "手机爱好者Lisa",
            "极客女孩", "数码博主小王", "测评师小李", "科技美少女"
        ]

        self.authors_weibo = [
            "数码测评官", "科技博主张三", "米粉大本营", "手机评测室",
            "极客公园", "数码圈内人", "科技前线", "评测达人"
        ]

        self.authors_twitter = [
            "TechReviewer", "XiaomiFanGlobal", "GadgetExpert", "MobileTechNews",
            "SmartphoneGeek", "TechInsider", "DigitalTrends", "PhoneReviewer"
        ]

        self.content_templates = [
            "用了{topic}，真的太{adj}了！{emoji} 特别是{feature}，简直{praise}！推荐给大家~",
            "说实话，{topic}确实{adj}。{feature}的表现{praise}，{emoji}性价比很高！",
            "刚入手{topic}，初步体验下来{adj}！{feature}特别{praise}，{emoji}值得购买！",
            "{topic}真的{adj}！{feature}这个设计太{praise}了，{emoji}必须好评！",
            "分享一下{topic}的使用感受：{adj}！特别是{feature}，{praise}得超出预期{emoji}",
        ]

        self.adjectives = ["不错", "惊艳", "给力", "优秀", "棒", "强大", "完美", "出色"]
        self.features = ["拍照", "续航", "性能", "屏幕", "充电速度", "系统流畅度", "外观设计", "握持手感"]
        self.praises = ["太棒了", "超预期", "很满意", "无可挑剔", "让人惊喜", "非常优秀", "值得点赞"]
        self.emojis = ["👍", "❤️", "🔥", "✨", "💯", "😍", "🎉", "⭐"]

    def generate_content(self, topic: str) -> str:
        """Generate realistic content"""
        template = random.choice(self.content_templates)
        return template.format(
            topic=topic,
            adj=random.choice(self.adjectives),
            feature=random.choice(self.features),
            praise=random.choice(self.praises),
            emoji=random.choice(self.emojis)
        )

    def generate_xiaohongshu_posts(self, count: int = 10) -> List[Dict]:
        """Generate demo Xiaohongshu posts"""
        posts = []
        for i in range(count):
            topic = random.choice(self.xiaomi_topics)
            author = random.choice(self.authors_xhs)

            post = {
                'platform': 'xiaohongshu',
                'post_id': f'xhs_demo_{i}_{random.randint(10000, 99999)}',
                'title': topic,
                'content': self.generate_content(topic),
                'author': author,
                'author_url': f'https://www.xiaohongshu.com/user/profile/{random.randint(1000000, 9999999)}',
                'post_url': f'https://www.xiaohongshu.com/discovery/item/{random.randint(1000000, 9999999)}',
                'image_urls': '',
                'video_url': '',
                'likes': random.randint(50, 5000),
                'comments': random.randint(10, 500),
                'shares': random.randint(5, 200),
                'views': random.randint(1000, 50000),
                'published_at': datetime.now() - timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                ),
            }
            posts.append(post)

        return posts

    def generate_weibo_posts(self, count: int = 10) -> List[Dict]:
        """Generate demo Weibo posts"""
        posts = []
        for i in range(count):
            topic = random.choice(self.xiaomi_topics)
            author = random.choice(self.authors_weibo)

            post = {
                'platform': 'weibo',
                'post_id': f'weibo_demo_{i}_{random.randint(10000, 99999)}',
                'title': '',
                'content': self.generate_content(topic),
                'author': author,
                'author_url': f'https://weibo.com/u/{random.randint(1000000, 9999999)}',
                'post_url': f'https://weibo.com/{random.randint(1000000, 9999999)}/{random.randint(1000000, 9999999)}',
                'image_urls': '',
                'video_url': '',
                'likes': random.randint(100, 10000),
                'comments': random.randint(20, 1000),
                'shares': random.randint(10, 500),
                'views': random.randint(5000, 100000),
                'published_at': datetime.now() - timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                ),
            }
            posts.append(post)

        return posts

    def generate_twitter_posts(self, count: int = 10) -> List[Dict]:
        """Generate demo Twitter posts"""
        posts = []
        for i in range(count):
            topic = random.choice(self.xiaomi_topics)
            author = random.choice(self.authors_twitter)

            # Twitter content is usually shorter
            content = f"Just tried {topic}! {random.choice(self.adjectives).capitalize()}! {random.choice(self.emojis)} #Xiaomi #Tech"

            post = {
                'platform': 'twitter',
                'post_id': f'twitter_demo_{i}_{random.randint(10000, 99999)}',
                'title': '',
                'content': content,
                'author': author,
                'author_url': f'https://twitter.com/{author.lower().replace(" ", "")}',
                'post_url': f'https://twitter.com/{author}/status/{random.randint(1000000000, 9999999999)}',
                'image_urls': '',
                'video_url': '',
                'likes': random.randint(50, 5000),
                'comments': random.randint(5, 200),
                'shares': random.randint(10, 500),
                'views': random.randint(1000, 50000),
                'published_at': datetime.now() - timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                ),
            }
            posts.append(post)

        return posts

    def generate_all_posts(self, count_per_platform: int = 10) -> List[Dict]:
        """Generate demo posts from all platforms"""
        all_posts = []
        all_posts.extend(self.generate_xiaohongshu_posts(count_per_platform))
        all_posts.extend(self.generate_weibo_posts(count_per_platform))
        all_posts.extend(self.generate_twitter_posts(count_per_platform))

        # Shuffle to mix platforms
        random.shuffle(all_posts)

        return all_posts
