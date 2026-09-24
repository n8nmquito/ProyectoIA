const groups = new Map();
for (const [index, item] of $input.all().entries()) {
  const origin = $('Separar adjuntos').itemMatching(index).json;
  const token = item.json.upload?.token;
  if (typeof token !== 'string' || !token) throw new Error('Redmine no devolvió el token para ' + origin.filename);
  if (!groups.has(origin.group)) groups.set(origin.group, { issue: { ...origin.issue, uploads: [] }, expected: origin.expected, pairedItem: [] });
  const group = groups.get(origin.group);
  group.issue.uploads.push({ token, filename: origin.filename, content_type: origin.content_type });
  group.pairedItem.push({ item: index });
}
return Array.from(groups.values(), group => {
  if (group.issue.uploads.length !== group.expected) throw new Error('Faltan adjuntos: se detiene la creación del ticket.');
  return { json: { issue: group.issue }, pairedItem: group.pairedItem };
});
