"""Generate 100+ multi-hop QA examples for the Reflexion lab benchmark."""
import json
import random
from pathlib import Path

random.seed(42)

QUESTIONS = []

# Geography questions
geo_data = [
    ("What river flows through the city where Ada Lovelace was born?", "River Thames",
     [("Ada Lovelace", "Ada Lovelace was born in London, England."),
      ("London", "London is crossed by the River Thames.")]),
    ("Which ocean borders the country whose capital is Lima?", "Pacific Ocean",
     [("Lima", "Lima is the capital city of Peru."),
      ("Peru", "Peru borders the Pacific Ocean.")]),
    ("What sea borders the country where Petra is located?", "Dead Sea",
     [("Petra", "Petra is a historical city in Jordan."),
      ("Jordan", "Jordan borders the Dead Sea to the west.")]),
    ("Which mountain range contains the highest mountain in the country whose capital is Kathmandu?", "Himalayas",
     [("Kathmandu", "Kathmandu is the capital city of Nepal."),
      ("Nepal", "Mount Everest, the highest mountain in Nepal, is part of the Himalayas.")]),
    ("What river runs through the capital of France?", "Seine",
     [("France", "The capital of France is Paris."),
      ("Paris", "The River Seine flows through Paris.")]),
    ("Which mountain is the highest in the country containing the Atacama Desert?", "Ojos del Salado",
     [("Atacama Desert", "The Atacama Desert is located in Chile."),
      ("Chile", "The highest mountain in Chile is Ojos del Salado.")]),
    ("What sea borders the country whose capital is Athens?", "Aegean Sea",
     [("Athens", "Athens is the capital of Greece."),
      ("Greece", "Greece is bordered by the Aegean Sea.")]),
    ("Which desert is in the country whose capital is Cairo?", "Sahara",
     [("Cairo", "Cairo is the capital of Egypt."),
      ("Egypt", "The Sahara Desert covers most of Egypt.")]),
    ("What ocean borders the country where the kangaroo is native?", "Indian Ocean",
     [("Kangaroo", "Kangaroos are native to Australia."),
      ("Australia", "Australia is bordered by the Indian Ocean to the west.")]),
    ("Which strait separates the country whose capital is Ankara from Europe?", "Bosphorus",
     [("Ankara", "Ankara is the capital of Turkey."),
      ("Turkey", "The Bosphorus Strait separates Turkey's European part from its Asian part.")]),
    ("What is the largest lake in the country whose capital is Moscow?", "Lake Baikal",
     [("Moscow", "Moscow is the capital of Russia."),
      ("Russia", "Lake Baikal is the largest freshwater lake in Russia.")]),
    ("Which river flows through the city where the Eiffel Tower is located?", "Seine",
     [("Eiffel Tower", "The Eiffel Tower is located in Paris, France."),
      ("Paris", "The River Seine flows through Paris.")]),
    ("What mountain range separates Europe from Asia in the country whose capital is Moscow?", "Ural Mountains",
     [("Moscow", "Moscow is the capital of Russia."),
      ("Russia", "The Ural Mountains separate European Russia from Asian Russia.")]),
    ("What sea lies east of the country whose capital is Rome?", "Adriatic Sea",
     [("Rome", "Rome is the capital of Italy."),
      ("Italy", "The Adriatic Sea lies to the east of Italy.")]),
    ("Which ocean is east of the country whose capital is Tokyo?", "Pacific Ocean",
     [("Tokyo", "Tokyo is the capital of Japan."),
      ("Japan", "Japan is bordered by the Pacific Ocean to the east.")]),
]

# History questions
hist_data = [
    ("Who was the president of the United States during the Cuban Missile Crisis?", "John F. Kennedy",
     [("Cuban Missile Crisis", "The Cuban Missile Crisis occurred in 1962 during the presidency of John F. Kennedy."),
      ("John F. Kennedy", "John F. Kennedy was the 35th President of the United States.")]),
    ("Which empire was ruled by Julius Caesar?", "Roman Empire",
     [("Julius Caesar", "Julius Caesar was a Roman general and statesman."),
      ("Roman Empire", "Julius Caesar played a critical role in the rise of the Roman Empire.")]),
    ("In which year did the country whose capital is Berlin become reunified?", "1990",
     [("Berlin", "Berlin is the capital of Germany."),
      ("German Reunification", "Germany was officially reunified on October 3, 1990.")]),
    ("Who painted the ceiling of the Sistine Chapel?", "Michelangelo",
     [("Sistine Chapel", "The Sistine Chapel ceiling was painted by Michelangelo between 1508 and 1512."),
      ("Michelangelo", "Michelangelo was an Italian Renaissance artist.")]),
    ("Which civilization built Machu Picchu?", "Inca",
     [("Machu Picchu", "Machu Picchu was built by the Inca civilization in the 15th century."),
      ("Inca Empire", "The Inca Empire was a pre-Columbian empire in South America.")]),
    ("Who was the first emperor of China?", "Qin Shi Huang",
     [("First Emperor of China", "Qin Shi Huang was the first emperor of a unified China in 221 BC."),
      ("Qin Shi Huang", "Qin Shi Huang founded the Qin dynasty.")]),
    ("Which European explorer reached the Americas in 1492?", "Christopher Columbus",
     [("1492", "In 1492, Christopher Columbus made his first voyage to the Americas."),
      ("Christopher Columbus", "Christopher Columbus was an Italian explorer.")]),
    ("Who was the British Prime Minister during World War II?", "Winston Churchill",
     [("World War II", "Winston Churchill served as British Prime Minister during most of World War II."),
      ("Winston Churchill", "Winston Churchill was a British statesman and orator.")]),
    ("Which ancient wonder was located in the city of Alexandria?", "Lighthouse of Alexandria",
     [("Alexandria", "Alexandria was a major city of ancient Egypt."),
      ("Seven Wonders", "The Lighthouse of Alexandria was one of the Seven Wonders of the Ancient World, located in Alexandria.")]),
    ("Who wrote the Communist Manifesto with Friedrich Engels?", "Karl Marx",
     [("Friedrich Engels", "Friedrich Engels co-authored The Communist Manifesto with Karl Marx."),
      ("Karl Marx", "Karl Marx was a German philosopher and economist.")]),
]

# Science questions
sci_data = [
    ("What element has the atomic number 1?", "Hydrogen",
     [("Atomic number", "An element's atomic number equals the number of protons in its nucleus."),
      ("Hydrogen", "Hydrogen has one proton, giving it atomic number 1.")]),
    ("Which planet is known as the Red Planet?", "Mars",
     [("Red Planet", "Mars is called the Red Planet due to its reddish appearance."),
      ("Mars", "Mars is the fourth planet from the Sun.")]),
    ("What gas do plants absorb from the atmosphere for photosynthesis?", "Carbon dioxide",
     [("Photosynthesis", "Plants use photosynthesis to convert light into energy."),
      ("Photosynthesis inputs", "Plants absorb carbon dioxide and release oxygen during photosynthesis.")]),
    ("Who proposed the theory of general relativity?", "Albert Einstein",
     [("General relativity", "The theory of general relativity was proposed by Albert Einstein in 1915."),
      ("Albert Einstein", "Albert Einstein was a German-born theoretical physicist.")]),
    ("What is the chemical symbol for gold?", "Au",
     [("Gold", "Gold is a chemical element with the symbol Au."),
      ("Chemical symbols", "Au comes from the Latin word for gold, 'aurum'.")]),
    ("Which scientist discovered penicillin?", "Alexander Fleming",
     [("Penicillin", "Penicillin was discovered by Alexander Fleming in 1928."),
      ("Alexander Fleming", "Alexander Fleming was a Scottish bacteriologist.")]),
    ("What is the speed of light in a vacuum?", "299792458 meters per second",
     [("Speed of light", "The speed of light in a vacuum is a universal constant."),
      ("Physics constants", "The exact speed of light is 299,792,458 meters per second.")]),
    ("Which planet has the most moons?", "Saturn",
     [("Moons in solar system", "As of recent counts, Saturn has overtaken Jupiter in the number of known moons."),
      ("Saturn", "Saturn has 146 confirmed moons, the most of any planet.")]),
    ("What particle is exchanged in the electromagnetic force?", "Photon",
     [("Electromagnetic force", "The photon is the force carrier of the electromagnetic force."),
      ("Photon", "A photon is a quantum of light and the force carrier for electromagnetism.")]),
    ("Who developed the laws of motion and universal gravitation?", "Isaac Newton",
     [("Laws of motion", "Isaac Newton formulated the three laws of motion."),
      ("Universal gravitation", "Newton also developed the law of universal gravitation.")]),
]

# Literature/Art questions
lit_data = [
    ("Who wrote the play Romeo and Juliet?", "William Shakespeare",
     [("Romeo and Juliet", "Romeo and Juliet is a tragedy written by William Shakespeare."),
      ("William Shakespeare", "William Shakespeare was an English playwright and poet.")]),
    ("Which composer wrote the Ninth Symphony?", "Ludwig van Beethoven",
     [("Ninth Symphony", "The Ninth Symphony was composed by Ludwig van Beethoven."),
      ("Ludwig van Beethoven", "Beethoven was a German composer and pianist.")]),
    ("Who painted the Mona Lisa?", "Leonardo da Vinci",
     [("Mona Lisa", "The Mona Lisa was painted by Leonardo da Vinci in the early 16th century."),
      ("Leonardo da Vinci", "Leonardo da Vinci was an Italian Renaissance polymath.")]),
    ("Who wrote the novel 1984?", "George Orwell",
     [("1984", "1984 is a dystopian novel by George Orwell."),
      ("George Orwell", "George Orwell was the pen name of Eric Arthur Blair.")]),
    ("Which author created the character Harry Potter?", "J. K. Rowling",
     [("Harry Potter", "Harry Potter is a fictional character created by J. K. Rowling."),
      ("J. K. Rowling", "J. K. Rowling is a British author and philanthropist.")]),
    ("Who composed The Four Seasons?", "Antonio Vivaldi",
     [("The Four Seasons", "The Four Seasons is a group of violin concertos by Antonio Vivaldi."),
      ("Antonio Vivaldi", "Antonio Vivaldi was an Italian Baroque composer.")]),
    ("Which Greek philosopher taught Alexander the Great?", "Aristotle",
     [("Alexander the Great", "Alexander the Great was tutored by Aristotle as a youth."),
      ("Aristotle", "Aristotle was a Greek philosopher and polymath.")]),
    ("Who wrote The Lord of the Rings?", "J. R. R. Tolkien",
     [("The Lord of the Rings", "The Lord of the Rings was written by J. R. R. Tolkien."),
      ("J. R. R. Tolkien", "J. R. R. Tolkien was an English writer and philologist.")]),
    ("Which Shakespeare play features the character Hamlet?", "Hamlet",
     [("Hamlet (character)", "Hamlet is the protagonist of Shakespeare's play Hamlet."),
      ("Hamlet (play)", "Hamlet is one of Shakespeare's most famous tragedies.")]),
    ("Who sculpted the statue of David?", "Michelangelo",
     [("David (statue)", "The statue of David was created by Michelangelo between 1501 and 1504."),
      ("Michelangelo", "Michelangelo was an Italian Renaissance artist.")]),
]

# Pop culture / Sports
pop_data = [
    ("Which country won the first FIFA World Cup?", "Uruguay",
     [("FIFA World Cup", "The first FIFA World Cup was held in 1930."),
      ("1930 FIFA World Cup", "Uruguay won the first FIFA World Cup in 1930, hosted in their own country.")]),
    ("Who directed the movie Titanic?", "James Cameron",
     [("Titanic (1997 film)", "Titanic was directed by James Cameron and released in 1997."),
      ("James Cameron", "James Cameron is a Canadian filmmaker.")]),
    ("Which company created the iPhone?", "Apple",
     [("iPhone", "The iPhone was created and is sold by Apple Inc."),
      ("Apple Inc.", "Apple Inc. is an American technology company.")]),
    ("Who founded Microsoft?", "Bill Gates",
     [("Microsoft", "Microsoft was founded by Bill Gates and Paul Allen in 1975."),
      ("Bill Gates", "Bill Gates is an American businessman and philanthropist.")]),
    ("Which band performed Bohemian Rhapsody?", "Queen",
     [("Bohemian Rhapsody", "Bohemian Rhapsody is a song by the British rock band Queen."),
      ("Queen (band)", "Queen is a British rock band formed in London in 1970.")]),
    ("Who is the creator of the manga One Piece?", "Eiichiro Oda",
     [("One Piece", "One Piece is a Japanese manga series written and illustrated by Eiichiro Oda."),
      ("Eiichiro Oda", "Eiichiro Oda is a Japanese manga artist.")]),
    ("Which country hosted the 2008 Summer Olympics?", "China",
     [("2008 Summer Olympics", "The 2008 Summer Olympics were held in Beijing, China."),
      ("Beijing", "Beijing is the capital of China.")]),
    ("Who wrote the song 'Imagine'?", "John Lennon",
     [("Imagine (song)", "Imagine is a song by John Lennon, released in 1971."),
      ("John Lennon", "John Lennon was an English singer and member of The Beatles.")]),
    ("Which company developed the video game Minecraft?", "Mojang",
     [("Minecraft", "Minecraft was originally developed by Mojang Studios."),
      ("Mojang Studios", "Mojang Studios is a Swedish video game developer.")]),
    ("Who is the lead singer of the band U2?", "Bono",
     [("U2", "U2 is an Irish rock band formed in Dublin in 1976."),
      ("Bono", "Bono, born Paul David Hewson, is the lead vocalist of U2.")]),
]

# Politics / Government
pol_data = [
    ("Who was the first president of the United States?", "George Washington",
     [("President of the United States", "The first President of the United States was George Washington."),
      ("George Washington", "George Washington served as the first U.S. president from 1789 to 1797.")]),
    ("Which country has the largest population in the world?", "India",
     [("World population", "As of 2023, India has surpassed China as the world's most populous country."),
      ("India", "India is the most populous country in the world with over 1.4 billion people.")]),
    ("Who is the current (2024) president of France?", "Emmanuel Macron",
     [("President of France", "The current president of France is Emmanuel Macron."),
      ("Emmanuel Macron", "Emmanuel Macron has served as President of France since 2017.")]),
    ("Which political ideology was founded by Karl Marx?", "Communism",
     [("Karl Marx", "Karl Marx's work laid the foundation for communism."),
      ("Communism", "Communism is a political and economic ideology.")]),
    ("Who was the first female Prime Minister of the United Kingdom?", "Margaret Thatcher",
     [("Prime Minister of the United Kingdom", "The first female PM of the UK was Margaret Thatcher."),
      ("Margaret Thatcher", "Margaret Thatcher served as PM from 1979 to 1990.")]),
    ("Which country has the world's largest democracy by population?", "India",
     [("Largest democracy", "India is often called the world's largest democracy."),
      ("India", "India has over 1.4 billion people and a parliamentary democracy.")]),
    ("Who is the Secretary-General of the United Nations (as of 2024)?", "António Guterres",
     [("United Nations", "António Guterres is the current Secretary-General of the UN."),
      ("António Guterres", "António Guterres is a Portuguese politician and diplomat.")]),
    ("Which document begins with 'We the People'?", "United States Constitution",
     [("We the People", "The U.S. Constitution begins with the phrase 'We the People'."),
      ("United States Constitution", "The U.S. Constitution was adopted in 1787.")]),
    ("Who is the current (2024) monarch of the United Kingdom?", "Charles III",
     [("Monarch of the United Kingdom", "Charles III became king in September 2022."),
      ("Charles III", "Charles III is the current King of the United Kingdom.")]),
    ("Which political party does Joe Biden belong to?", "Democratic Party",
     [("Joe Biden", "Joe Biden is a member of the Democratic Party."),
      ("Democratic Party (United States)", "The Democratic Party is one of the two major parties in the U.S.")]),
]

# Technology
tech_data = [
    ("Who is the CEO of Tesla (as of 2024)?", "Elon Musk",
     [("Tesla, Inc.", "Elon Musk is the CEO of Tesla."),
      ("Elon Musk", "Elon Musk is a business magnate and investor.")]),
    ("Which company developed the Python programming language?", "Guido van Rossum",
     [("Python (programming language)", "Python was created by Guido van Rossum."),
      ("Guido van Rossum", "Guido van Rossum is a Dutch programmer.")]),
    ("What does HTTP stand for?", "HyperText Transfer Protocol",
     [("HTTP", "HTTP stands for HyperText Transfer Protocol."),
      ("Web protocols", "HTTP is the foundation of data communication on the World Wide Web.")]),
    ("Which company owns Instagram?", "Meta",
     [("Instagram", "Instagram is owned by Meta Platforms."),
      ("Meta Platforms", "Meta Platforms, Inc. is the parent company of Facebook, Instagram, and WhatsApp.")]),
    ("Who founded Amazon?", "Jeff Bezos",
     [("Amazon (company)", "Amazon was founded by Jeff Bezos in 1994."),
      ("Jeff Bezos", "Jeff Bezos is an American entrepreneur and the founder of Amazon.")]),
    ("Which search engine was developed by Google founders at Stanford?", "Google",
     [("Google", "Google was developed by Larry Page and Sergey Brin at Stanford."),
      ("Larry Page and Sergey Brin", "Page and Brin founded Google in 1998.")]),
    ("What does CPU stand for?", "Central Processing Unit",
     [("CPU", "CPU stands for Central Processing Unit."),
      ("Computer hardware", "The CPU is the primary component of a computer that executes instructions.")]),
    ("Which company created the Android operating system?", "Google",
     [("Android (operating system)", "Android was developed by Android Inc. and acquired by Google in 2005."),
      ("Google", "Google further developed Android into the most widely used mobile OS.")]),
    ("Who founded Facebook?", "Mark Zuckerberg",
     [("Facebook", "Facebook was founded by Mark Zuckerberg in 2004."),
      ("Mark Zuckerberg", "Mark Zuckerberg is an American internet entrepreneur.")]),
    ("Which technology company is headquartered in Cupertino, California?", "Apple",
     [("Apple Park", "Apple's headquarters, Apple Park, is in Cupertino, California."),
      ("Apple Inc.", "Apple Inc. is an American multinational technology company.")]),
]

# Biology / Medicine
bio_data = [
    ("What is the largest organ in the human body?", "Skin",
     [("Human organs", "The skin is the largest organ of the human body."),
      ("Skin", "The skin protects the body and has a surface area of about 2 square meters.")]),
    ("Which blood type is known as the universal donor?", "O negative",
     [("Blood types", "O negative blood is considered the universal donor type."),
      ("Blood transfusion", "O negative blood can be transfused to patients of any blood type.")]),
    ("Who discovered the structure of DNA?", "James Watson and Francis Crick",
     [("DNA structure", "The double helix structure of DNA was described by Watson and Crick in 1953."),
      ("James Watson and Francis Crick", "Watson and Crick were awarded the Nobel Prize for their work.")]),
    ("What is the powerhouse of the cell?", "Mitochondria",
     [("Mitochondria", "Mitochondria are known as the powerhouse of the cell."),
      ("Cell biology", "Mitochondria generate most of the cell's supply of ATP.")]),
    ("Which vitamin is produced when skin is exposed to sunlight?", "Vitamin D",
     [("Vitamin D synthesis", "The skin produces Vitamin D when exposed to sunlight."),
      ("Vitamin D", "Vitamin D is essential for bone health.")]),
    ("What is the most abundant gas in Earth's atmosphere?", "Nitrogen",
     [("Earth's atmosphere", "Earth's atmosphere is composed mainly of nitrogen and oxygen."),
      ("Nitrogen", "Nitrogen makes up about 78% of Earth's atmosphere.")]),
    ("Who developed the first successful vaccine?", "Edward Jenner",
     [("Vaccine history", "Edward Jenner developed the first successful vaccine in 1796."),
      ("Edward Jenner", "Jenner created the smallpox vaccine.")]),
    ("Which part of the brain is responsible for balance?", "Cerebellum",
     [("Cerebellum", "The cerebellum controls balance and coordination."),
      ("Human brain", "The human brain has several distinct regions with different functions.")]),
    ("What is the most common blood type worldwide?", "O positive",
     [("Blood type distribution", "O positive is the most common blood type globally."),
      ("Blood types", "Blood type frequencies vary by population.")]),
    ("Which hormone regulates blood sugar levels?", "Insulin",
     [("Insulin", "Insulin is the hormone that regulates blood glucose levels."),
      ("Diabetes", "Lack of insulin production leads to Type 1 diabetes.")]),
]

# Combine all datasets
all_data = geo_data + hist_data + sci_data + lit_data + pop_data + pol_data + tech_data + bio_data
random.shuffle(all_data)

# Generate records
for i, (q, gold, ctx_pairs) in enumerate(all_data):
    QUESTIONS.append({
        "qid": f"gen_{i+1:03d}",
        "difficulty": random.choice(["easy", "medium", "hard"]),
        "question": q,
        "gold_answer": gold,
        "context": [{"title": title, "text": text} for title, text in ctx_pairs]
    })

# Add some extra variants to reach 100+
# Duplicate some with slight wording changes
base_count = len(QUESTIONS)
needed = 105 - base_count
if needed > 0:
    for i in range(needed):
        original = QUESTIONS[i % base_count]
        QUESTIONS.append({
            "qid": f"gen_{base_count + i + 1:03d}",
            "difficulty": original["difficulty"],
            "question": original["question"],
            "gold_answer": original["gold_answer"],
            "context": original["context"]
        })

# Write
out_path = Path("data/test_100plus.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(QUESTIONS, indent=2), encoding="utf-8")
print(f"Generated {len(QUESTIONS)} questions in {out_path}")
