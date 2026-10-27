#!/usr/bin/env python3
"""Build the combined PDF and editable Markdown from JSON sources.

Requires reportlab only for report generation, not for the Sudoku solver.
Run from any working directory: python3 report/build_report.py
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

ROOT = Path(__file__).resolve().parents[1]
meta = json.loads((ROOT/'report/metadata.json').read_text())
content = json.loads((ROOT/'report/content.json').read_text())
bench = json.loads((ROOT/'Sudoku/evaluation/benchmark.json').read_text())
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyC',fontName='Helvetica',fontSize=11,leading=14.2,spaceAfter=9,textColor=HexColor('#243143')))
styles.add(ParagraphStyle(name='SubC',fontName='Helvetica-Bold',fontSize=11.3,leading=14.3,spaceBefore=4,spaceAfter=4,textColor=HexColor('#123B4B')))
styles.add(ParagraphStyle(name='TitleC',fontName='Helvetica-Bold',fontSize=22,leading=26,spaceAfter=16,textColor=HexColor('#123B4B')))
styles.add(ParagraphStyle(name='CoverC',fontName='Helvetica-Bold',fontSize=31,leading=36,spaceAfter=16,textColor=HexColor('#123B4B')))
styles.add(ParagraphStyle(name='KickerC',fontName='Helvetica-Bold',fontSize=11,leading=14,spaceAfter=8,textColor=HexColor('#36818C')))
styles.add(ParagraphStyle(name='CodeC',fontName='Courier',fontSize=11,leading=13.5,spaceBefore=3,spaceAfter=10,textColor=HexColor('#243143')))
styles.add(ParagraphStyle(name='LinkC',fontName='Helvetica',fontSize=11,leading=14.2,spaceAfter=7,textColor=HexColor('#246D85'),splitLongWords=True))

story=[]
md=[]
def p(text,style='BodyC'):
    return Paragraph(escape(text),styles[style])
def table(rows,widths):
    tab=Table(rows,colWidths=[x*cm for x in widths],hAlign='LEFT')
    tab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),HexColor('#123B4B')),
        ('TEXTCOLOR',(0,0),(-1,0),white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,0),(-1,-1),11),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#EAF2F4'),HexColor('#F6F8FA')])]))
    return tab

def table_markdown(rows):
    return '\n'.join(['| '+' | '.join(rows[0])+' |', '| '+' | '.join(['---']*len(rows[0]))+' |']+
                     ['| '+' | '.join(row)+' |' for row in rows[1:]])

story.extend([Spacer(1,12),p(meta['course'],'KickerC'),Spacer(1,15),p(meta['title'],'CoverC'),p(meta['subtitle'],'TitleC'),Spacer(1,20)])
md.extend(['# '+meta['title'],'\n'+meta['course']+'\n\n'+meta['subtitle']+'\n'])
for member in meta['members']:
    story.extend([p(member['name'],'SubC'),p(member['id'])])
    md.append(f"- {member['name']} - {member['id']}")
story.append(Spacer(1,18))
for label,key in [('Canvas group / campus','canvas_group'),('Video demonstration','video_url')]:
    story.extend([p(label,'SubC'),p(meta[key])])
    md.append(f'\n**{label}:** {meta[key]}\n')
story.extend([Spacer(1,18),p('Use of Generative AI','SubC'),p(meta['genai_statement']),Spacer(1,12),p('Report structure','SubC'),p('Part 1: CSP modelling, implementation, evaluation and theoretical A* analysis (four pages). Part 2: PDDL modelling, missions and astronaut extension (three pages). References follow separately.'),Spacer(1,10),p(meta['date'])])
md.extend(['\n## Use of Generative AI\n',meta['genai_statement']+'\n'])

for page in content['pages']:
    story.extend([PageBreak(),p(page['part']+' / F29AI COURSEWORK 1','KickerC'),p(page['title'],'TitleC')])
    md.append('\n## '+page['part']+': '+page['title']+'\n')
    for block in page['blocks']:
        story.append(p(block['heading'],'SubC'))
        md.append('\n### '+block['heading']+'\n')
        if 'text' in block:
            story.append(p(block['text']))
            md.append(block['text']+'\n')
        elif 'code' in block:
            story.append(Preformatted(block['code'],styles['CodeC']))
            md.append('```text\n'+block['code']+'\n```\n')
        elif block['table']=='sudoku':
            rows=[['Case','Givens','Median ms','Guesses','Backtracks','Result']]
            for row in bench['summary']:
                rows.append([row['label'],str(row['givens']),f"{row['median_ms']:.3f}",f"{row['guesses']:,}",f"{row['backtracks']:,}",'Solved' if row['status']=='solved' else 'No solution'])
            story.extend([table(rows,[3.5,1.5,2.3,2.3,2.5,2.7]),Spacer(1,9)])
            md.append(table_markdown(rows)+'\n')
        else:
            rows=[['Mission','Actions','Delivery goals','Full replay'],['1','10','3 of 3','Pass'],['2','20','6 of 6','Pass'],['3','24','6 of 6','Pass']]
            story.extend([table(rows,[3.4,3.1,4.4,4.1]),Spacer(1,9)])
            md.append(table_markdown(rows)+'\n')

story.extend([PageBreak(),p('SOURCES / F29AI COURSEWORK 1','KickerC'),p('References','TitleC')])
md.append('\n## References\n')
for ref in content['references']:
    story.append(p(ref['label'],'SubC'))
    if ref['url']:
        url=escape(ref['url'],{'"':'&quot;'})
        story.append(Paragraph(f'<link href="{url}">{url}</link>',styles['LinkC']))
    story.extend([p(ref['note']),Spacer(1,12)])
    md.append(ref['label']+'\n\n'+(ref['url']+'\n\n' if ref['url'] else '')+ref['note']+'\n')

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(HexColor('#CCD9DF'))
    canvas.line(2*cm,1.65*cm,A4[0]-2*cm,1.65*cm)
    canvas.setFont('Helvetica',9)
    canvas.setFillColor(HexColor('#526474'))
    canvas.drawString(2*cm,1.15*cm,'F29AI  |  Search and Automated Planning')
    canvas.drawRightString(A4[0]-2*cm,1.15*cm,str(doc.page))
    canvas.restoreState()

pdf=ROOT/'Coursework_Report.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,
                      topMargin=2*cm,bottomMargin=2*cm,title=meta['title'],
                      author='; '.join(m['name'] for m in meta['members']))
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'Coursework_Report.md').write_text('\n'.join(md)+'\n')
print(pdf)
