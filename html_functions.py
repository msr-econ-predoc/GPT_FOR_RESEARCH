
import os
import pandas as pd
import seaborn as sns
import json
from bs4 import BeautifulSoup, NavigableString

def make_tab_table(tables):
    table_soups = [BeautifulSoup(table, 'html.parser') for table in tables]

    soup = BeautifulSoup('<div></div>', 'html.parser')
    tabs_div = soup.div

    # Create the tab navigation
    nav_tabs = soup.new_tag('ul', **{'class': 'nav nav-tabs', 'role': 'tablist'})
    tabs_div.append(nav_tabs)

    # Create the tab content area
    tab_content = soup.new_tag('div', **{'class': 'tab-content'})
    tabs_div.append(tab_content)

    for index, table_soup in enumerate(table_soups, start=1):
        # Create a tab for each table
        tab_id = f'table-tab-{index}'
        nav_item = soup.new_tag('li', **{'class': 'nav-item'})
        nav_link = soup.new_tag('a', **{
            'class': 'nav-link' + (' active' if index == 1 else ''),  # Mark the first tab as active
            'id': f'{tab_id}-tab',
            'data-toggle': 'tab',
            'href': f'#{tab_id}',
            'role': 'tab',
            'aria-controls': tab_id,
            'aria-selected': 'true' if index == 1 else 'false'
        })
        nav_link.string = f'Table {index}'
        nav_item.append(nav_link)
        nav_tabs.append(nav_item)

        # Create a tab pane for each table
        tab_pane = soup.new_tag('div', **{
            'class': 'tab-pane fade' + (' show active' if index == 1 else ''),  # Mark the first pane as active
            'id': tab_id,
            'role': 'tabpanel',
            'aria-labelledby': f'{tab_id}-tab'
        })
        # Add the 'table-striped' and 'table-hover' classes to the table
        table_soup.table['class'] = table_soup.table.get('class', []) + ['table', 'table-striped', 'table-hover']
        tab_pane.append(table_soup.table)
        tab_content.append(tab_pane)


    return soup


def make_final_html(soup, path):
    # Parse the HTML
    tables = soup.find_all('table')

    # Create the <style> tag with your CSS
    style_tag = soup.new_tag("style")
    style_tag.string = """
    details > summary {
    cursor: pointer;
    font-weight: bold;
    }
    .hidden-content {
    display: none;
    }
    details[open] .hidden-content {
    display: block;
    }
    select {
    /* Style adjustments for the dropdown */
    padding: 5px;
    margin: 0;
    border-radius: 5px;
    }
    """

    # Add the Bootstrap CSS link
    bootstrap_link_tag = soup.new_tag('link', href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css", rel="stylesheet", integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH", crossorigin="anonymous")
    
    # Add jQuery and Bootstrap JS scripts
    jquery_script_tag = soup.new_tag("script", src="https://code.jquery.com/jquery-3.3.1.slim.min.js")
    jquery_script_tag.attrs['integrity'] = "sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
    jquery_script_tag.attrs['crossorigin'] = "anonymous"

    popper_script_tag = soup.new_tag("script", src="https://cdn.jsdelivr.net/npm/popper.js@1.14.7/dist/umd/popper.min.js")
    popper_script_tag.attrs['integrity'] = "sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1"
    popper_script_tag.attrs['crossorigin'] = "anonymous"

    bootstrap_script_tag = soup.new_tag("script", src="https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/js/bootstrap.min.js")
    bootstrap_script_tag.attrs['integrity'] = "sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM"
    bootstrap_script_tag.attrs['crossorigin'] = "anonymous"

    # Create the <head> tag and insert the <style> tag inside it
    head_tag = soup.new_tag("head")
    head_tag.insert(0, style_tag)
    head_tag.insert(1, bootstrap_link_tag)

    # If the document already has a <head> tag, replace it. Otherwise, insert the new <head> tag at the beginning
    existing_head = soup.head
    if existing_head:
        existing_head.replace_with(head_tag)
    else:
        soup.insert(0, head_tag)

    # Insert the scripts at the end of the body
    body_tag = soup.body
    if body_tag:
        body_tag.append(jquery_script_tag)
        body_tag.append(popper_script_tag)
        body_tag.append(bootstrap_script_tag)
    else:
        soup.append(jquery_script_tag)
        soup.append(popper_script_tag)
        soup.append(bootstrap_script_tag)

    for i, td in enumerate(soup.find_all('td', string=lambda text: text in ['select'])):
        # Clear the existing content
        k = (i + 1) % 6
        j = (i + 1) // 6

        if td.string == 'select':
            td.clear()
            dropdown_html = BeautifulSoup(f"""
        <select id="0_{j}_{k}">
        <option value="0">select</option>
        <option value="1">0</option>
        <option value="2">1</option>
        </select>
        """, 'html.parser')
            # Insert the dropdown
            td.append(dropdown_html.select_one('select'))

    # Convert back to HTML string
    edited_html_table = str(soup)
    with open(path, 'w') as f:
        f.write(edited_html_table)