import discord
from glob import glob
from datetime import date, timedelta
import json
import os 
from discord.ext import commands
import sympy
import matplotlib.pyplot as plt
from sympy import latex
from io import BytesIO
import random
from cryptography.fernet import Fernet
from pdf2image import convert_from_path


started_tasks = {}


phrases = [
    "Das rahme ich mir ein!",
    "Edel!",
    "Ob8!",
    "Gleich rollt der Pudel",
    "Das ist schon eine ganz andere Erdbeere",
    "Dann zeigen wir mal, wo der Frosch die Locken hat",
    "Das ist wie Erbsen essen, das geht von ganz alleine",
    "Das ist edel möchte jemand einen freiwilligen Vortrag machen, man kann sich nur verbessern.",
]

failes = [
    "Das ist für die Freaks.",
    "Das machen wir nächste Stunde.",
    "Sowas hat auch noch niemand gemacht",
]


key = os.environ.get("ENCRYPTION_KEY_DISCORD")
if key == None:
    print("Couldn't find a Key")
    print("Create an Encryption Key")
    print("Add Encryption key to enviroment Variable")
    print(Fernet.generate_key())
    print("-> ENCRYPTION_KEY_DISCORD")
    exit()


key=key.replace(" ", "")
key = key.encode()
fernet = Fernet(key)

intents = discord.Intents.all()

if not os.path.exists("discord.secret"):
    token = (fernet.encrypt(input("Input Discord Token => ").encode())).decode()
    with open("discord.secret", "w") as f:
        f.write(token)

with open("discord.secret") as f:
    token = fernet.decrypt(f.read().encode()).decode()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    now = date.today()
    file_path = f"saved{now}.json"
    if os.path.exists(file_path):
        pass
    else: 
        with open(file_path, 'w') as file:
            yesterday = now - timedelta(days=1)
            if not os.path.exists(f"./saved{yesterday}.json"):
                file.write("{}")
                return

            with open(f"./saved{yesterday}.json", "r") as file:
                data = json.loads(file.read())

            today = {}
            for user in data:
                today[user] = {
                    "Goal": data[user]["Goal"],
                    "Done": 0,
                }
            json.dump(today, file)




async def random_text(ctx):
    await ctx.send(random.choice(phrases))

def to_latex(formula, length):
    arr = [len(x.atoms()) for x in formula]
    max_len = max(arr)
    try:
        formula = [f"${latex(f)}$" for f in formula]
    except Exception:
        formula = [f"${latex(f.evalf())}$" for f in formula]


    _, ax = plt.subplots(figsize=(max_len, length))

    if len(formula) > 1:
        for i, solution in enumerate(formula):
            ax.text(0.5, (len(formula) - i)/len(formula) - 0.1, f"{solution}", size=20, ha='center', va='center')
    else:
        ax.text(0.5, 0.5,  f"{formula[0]}", size=20, ha='center', va='center')

    ax.axis('off')
    try:
        plt.tight_layout()
    except Exception:
        pass
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches="tight")
    buffer.seek(0)
    plt.close()
    return buffer

@bot.command()
async def goal(ctx, num):
    author = f"{ctx.author.id}"
    num = int(num)
    path = f"./saved{date.today()}.json"

    if not os.path.exists(path):
        with open(path, 'w') as file:
            pass

    with open(path, "r") as file:
        try:
            data = json.loads(file.read())
        except:
            data = {}

    if data is None:
        data = {
            author: {
                "Goal": num,
                "Done": 0,
            }
        }

    try:
        data[author]
    except:
        data[author] = {
            "Goal": num,
            "Done": 0
        }

    current = data[author] 
    current["Goal"] = num
    data[author] = current

    with open(path, "w") as file:
        json.dump(data, file)

@bot.command()
async def done(ctx):
    author = f"{ctx.author.id}"
    path = f"./saved{date.today()}.json"

    try:
        started_tasks[author]
    except:
        await ctx.send("Starte eine Aufgabe")
        return

    if started_tasks[author] == 0:
        await ctx.send("Starte eine Aufgabe")
        return

    with open(path, "r") as file:
        data = json.loads(file.read())

    try:
        data[author]
    except:
        data[author] = {
            "Goal": 0,
            "Done": 0,
        }

    current = data[author] 
    current["Done"] += 1
    done = current["Done"]
    goal = current["Goal"]
    if done >= goal:
        await ctx.send(f"du hast {done} Aufgaben geschafft :thumbsup:")
    else:
        await ctx.send(f"Du hast [{done}/{goal}] Aufgaben Geschafft!!")
    data[author] = current

    started_tasks[author] = 0

    with open(path, "w") as file:
        json.dump(data, file)

@bot.command()
async def diary(ctx):
    author = f"{ctx.author.id}"
    arr1 = []
    arr2 = []
    time = []
    for file_path in glob("./*.json"):
        with open(file_path, "r") as file:
            content = file.read()
            print(content)
            if content == "":
                content = "{}"

            data = json.loads(content)
            s = file_path.replace("./saved", "")
            s = s.replace(".json", "")
            try:
                arr1.append(data[author]["Done"])
                arr2.append(data[author]["Goal"])
                time.append(s)
            except:
                pass

    plt.bar(x=time, height=arr2, width=0.2, label="Ziel", color="red")
    plt.bar(x=time, height=arr1, width=0.2, label="Geschaft", color="#4de44d", edgecolor="black", linewidth=1.2, capstyle="round")
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()

    await ctx.send(file=discord.File(buffer, "plot.png"))
                



@bot.command()
async def plot(ctx, function: str):
    function = function.replace("^", "**")
    eq = sympy.sympify(function)
    graph = sympy.plot(eq, show=False, xlabel="", ylabel="", xlim=(-3, 3))
    buffer = BytesIO()
    graph.save(buffer)
    buffer.seek(0)

    await ctx.send(file=discord.File(buffer, "plot.png"))



@bot.command()
async def kurvendiskussion(ctx, function: str):
    await random_text(ctx)
    function = function.replace("^", "**")
    eq = sympy.sympify(function)
    x = sympy.symbols("x")
    solutions = sympy.solve(sympy.Eq(eq, 0), x)
    solutions = [sol.evalf() for sol in solutions]
    buffer = to_latex(solutions, len(solutions))
    await ctx.send("X-Schnittpunkte")
    await ctx.send(file=discord.File(buffer, "plot.png"))

    zero = eq.evalf(subs={x:0})

    buffer = to_latex([zero], 1)
    await ctx.send("Y-Schnittpunkt")
    await ctx.send(file=discord.File(buffer, "plot.png"))
    await random_text(ctx)

    deriv = eq.diff()
    extrm = sympy.solve(sympy.Eq(deriv, 0), x)
    second_deriv = deriv.diff()
    extrms = {}
    for sol in extrm:
        val = second_deriv.evalf(subs={x:sol})

        try:
            if val < 0:
                extrms[sol] = ["Hochpunkt", eq.evalf(subs={x:sol})]
            elif val > 0:
                extrms[sol] = ["Tiefpunkt", eq.evalf(subs={x:sol})]
        except Exception:
            pass
        
    i=1
    for ext in extrms:
        vals = extrms[ext]
        typ = vals[0]
        val = vals[1]
        await ctx.send(str("```" +str(i) + "." + typ + "(" + str(f"{ext.evalf():.3f}") + "|" + str(f"{val:.3f}") + ")" + "```"))
        i+=1
    await random_text(ctx)
    
    turn = sympy.solve(sympy.Eq(second_deriv, 0), x)
    third_deriv = deriv.diff()
    turns = {}
    for t in turn:
        val = third_deriv.evalf(subs={x:t})
        try:
            if val != 0:
                turns[t] = eq.evalf(subs={x:t})
        except Exception:
            pass
    
    i = 1
    for t in turns:
        await ctx.send(str("```"+str(i) + ".Wendepunkt" +"(" + str(f"{t}") + "|" + str(f"{turns[t]}") + ")" + "```"))
        i+=1
    await random_text(ctx)


@bot.command()
async def lernapotheke(ctx):
    string = """
    ->
    !integral [Funktion] -> Bildet Stammfunktion

    !derivative [Funktion] -> Bildet Ableitung

    !solve [Gleichung] [Variable] -> löst die Gleichung nach der Variable auf

    !plot [Funktion] -> Zeichnet die Funktion

    !aufgabe {analysis, ag, stochastik, _} {OHIMI, CAS} -> gibt eine Mathe Aufgabe

    !goal  -> Setze ein Ziel wie viele Aufgaben du am Tag rechnen willst
    !done  -> Du bist Fertig mit deiner Aufgabe
    !diary -> Zeigt dir deine Erfolge der Vergangenheit

    """
    await ctx.send(string)

@bot.command()
async def aufgabe(ctx, question_type: str="", ohimi = ""):
    temp = True
    dir = os.listdir("./Aufgaben")

    f = ""

    if question_type == "_":
        question_type = ""

    while temp:
        f = random.choice(dir)
        temp = question_type.upper() not in f.upper()
        if ohimi.upper() == "CAS":
            temp = temp or ("CAS" not in f.upper() and "MMS" not in f.upper())
        else:
            temp = temp or ("CAS" in f.upper() or "MMS" in f.upper())

    file_path = "./Aufgaben/" + f
    images = convert_from_path(file_path)

    started_tasks[f"{ctx.author.id}"] = 1

    for image in images:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, "Aufgabe.png"))


@bot.command()
async def plot3d(ctx, function: str):
    function = function.replace("^", "**")
    eq = sympy.sympify(function)
    graph = sympy.plotting.plot3d(eq, show=False)

    buffer = BytesIO()
    graph.save(buffer)
    buffer.seek(0)

    await ctx.send(file=discord.File(buffer, "plot.png"))

@bot.command()
async def derivative(ctx, function: str):


    if random.random() < 0.05:
        await ctx.send("Das guck ich mir zuhause an.")
        return

    function = function.replace("^", "**")
    eq = sympy.sympify(function) 
    try:
        der = sympy.simplify(eq.diff())
    except Exception:
        await ctx.send(random.choice(failes))
        return

    derT = sympy.Eq(sympy.Derivative(eq), der)

    buffer = to_latex([derT], 2)

    await random_text(ctx)
    await ctx.send(file=discord.File(buffer, "derivative.png"))
    string = str(der).replace("**", "^").replace(" ", "")
    await ctx.send("```"+ string +"```")



@bot.command()
async def integral(ctx, function:str):
    """Des"""
    if random.random() < 0.05:
        await ctx.send("Das guck ich mir zuhause an.")
        return
    function = function.replace("^", "**")
    eq = sympy.sympify(function)
    try:
        integ = sympy.simplify(sympy.integrate(sympy.simplify(eq)))
    except Exception:
        await ctx.send(random.choice(failes))
        return

    integT = sympy.Eq(sympy.Integral(eq), integ)
    buffer = to_latex([integT], 1)

    await random_text(ctx)
    await ctx.send(file=discord.File(buffer, "integral.png"))
    string = str(integ).replace("**", "^")
    string = string.replace(" ", "")
    await ctx.send("```"+ string +"```")


@bot.command()
async def solve(ctx, equation:str, variable:str):

    if random.random() < 0.05:
        await ctx.send("Das guck ich mir zuhause an.")
        return
    equation = equation.replace("^", "**")
    equation = equation.split("=")

    var = sympy.symbols(variable)
    variable = str(variable)

    try:
        eq = sympy.Eq(sympy.sympify(equation[0]), sympy.sympify(equation[1]))
        solutions = sympy.solve(eq, var)
    except Exception as e:
        print(e)
        await ctx.send(random.choice(failes))
        return
    solutions = [sympy.simplify(solution) for solution in solutions]

    buffer = to_latex(solutions, len(solutions) -1)

    await random_text(ctx)

    await ctx.send(file=discord.File(buffer, "solutions.png"))

bot.run(token=token)
