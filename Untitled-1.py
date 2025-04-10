import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
import asyncio

# === 설정 ===
TOKEN = "MTM1OTc5ODA1NTQzOTgzMTA5MA.GUMg5-.WCqW6Bu-vql-PfxFjvGEqp0ExzneNI5eJLstVc"  # 토큰은 안전하게 환경변수나 config 파일에서 관리하세요.
CATEGORY_ID = 1359822770887856138
ASSIGN_ROLE_IDS = [1359828854440595530]  # 리스트 형태로 변경
CITIZEN_ROLE_ID = 1356276050354769985

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


def is_admin(member: discord.Member):
    return any(role.id in ASSIGN_ROLE_IDS for role in member.roles)


@bot.event
async def on_member_join(member):
    role = member.guild.get_role(CITIZEN_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"{member}에게 시민 역할 지급 완료")


@bot.event
async def on_ready():
    for guild in bot.guilds:
        await tree.sync(guild=guild)
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if category:
            for channel in category.text_channels:
                try:
                    await send_ticket_button(channel)
                    break
                except Exception as e:
                    print(f"버튼 전송 실패: {e}")
        else:
            print("카테고리 없음")
    print(f"봇 실행됨: {bot.user}")


class TicketButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="문의 시작하기", style=discord.ButtonStyle.primary, custom_id="create_ticket"))


async def send_ticket_button(channel):
    embed = discord.Embed(title="🌻 문의 시스템", description="아래 버튼을 눌러 문의를 시작하세요.", color=discord.Color.blurple())
    await channel.send(embed=embed, view=TicketButtonView())


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data["custom_id"]
    guild = interaction.guild
    member = interaction.user  # 이 부분 수정됨

    if custom_id == "create_ticket":
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        existing = discord.utils.find(lambda c: c.name == f"ticket-{member.id}", category.text_channels)
        if existing:
            await interaction.response.send_message("이미 열려있는 문의가 있습니다!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role_id in ASSIGN_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.id}",
            category=category,
            overwrites=overwrites,
            topic=f"{member}의 문의 채널",
        )

        embed = discord.Embed(title="🕐 담당자 배정 대기 중", description="관리자가 곧 배정될 예정입니다.\n무례한 태도는 제재될 수 있습니다.", color=discord.Color.blue())
        assign_button = Button(label="담당자 배정하기", style=discord.ButtonStyle.primary, custom_id="assign_button")
        view = View()
        view.add_item(assign_button)

        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"{ticket_channel.mention} 채널에서 문의를 진행해주세요.", ephemeral=True)

    elif custom_id == "assign_button":
        if is_admin(member):
            embed = discord.Embed(title="✅ 담당자 배정 완료", description=f"{member.mention} 님이 담당자로 배정되었습니다.", color=discord.Color.green())
            close_button = Button(label="문의 종료하기", style=discord.ButtonStyle.danger, custom_id="close_ticket")
            view = View()
            view.add_item(close_button)
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.send_message("담당자로 배정되었습니다!", ephemeral=True)
        else:
            await interaction.response.send_message("이 버튼을 누를 권한이 없습니다.", ephemeral=True)

    elif custom_id == "close_ticket":
        if is_admin(member):
            embed = discord.Embed(title="📉 문의 종료됨", description="이 채널은 곧 삭제됩니다.", color=discord.Color.red())
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message("문의가 종료되었습니다.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("이 버튼을 누를 권한이 없습니다.", ephemeral=True)


# ================= 슬래시 명령어 ==================

@tree.command(name="서버오픈", description="청해군 공지를 출력합니다 (관리자 전용)")
async def announce_notice(interaction: discord.Interaction):
    member = interaction.user  # 수정됨
    if not is_admin(member):
        await interaction.response.send_message("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    citizen_role = interaction.guild.get_role(CITIZEN_ROLE_ID)
    await interaction.response.send_message(f"{citizen_role.mention} 청해군 서버가 열렸어요! 청해군에 들어와 청해군을 플레이 해요..")


@tree.command(name="공무원", description="청해군 공무원 전용 메시지 출력 (관리자 전용)")
async def announce_officer(interaction: discord.Interaction):
    member = interaction.user  # 수정됨
    if not is_admin(member):
        await interaction.response.send_message("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    await interaction.response.send_message("공무원 입장시간입니다.")


@tree.command(name="운수업", description="청해군 공무원 전용 메시지 출력 (관리자 전용)")
async def announce_bustaxi(interaction: discord.Interaction):
    member = interaction.user  # 수정됨
    if not is_admin(member):
        await interaction.response.send_message("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    await interaction.response.send_message("운수업 입장시간입니다.")


@tree.command(name="kick", description="지정한 유저를 서버에서 강퇴합니다. (관리자 전용)")
@app_commands.describe(user="강퇴할 유저", reason="강퇴 사유")
async def kick_user(interaction: discord.Interaction, user: discord.Member, reason: str = "사유 없음"):
    member = interaction.user  # 수정됨
    if not is_admin(member):
        await interaction.response.send_message("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"{user.mention}님을 강퇴했습니다. 사유: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"강퇴에 실패했습니다: {e}", ephemeral=True)

# ===================================================

bot.run(TOKEN)
