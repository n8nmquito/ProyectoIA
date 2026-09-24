const output = [];
for (const [group, item] of $input.all().entries()) {
  const files = Object.entries(item.binary || {});
  for (const [key, file] of files) {
    const name = String(file.fileName || key).replace(/[\\/\x00-\x1f]/g, '_').slice(0, 200) || 'adjunto';
    output.push({
      json: { group, expected: files.length, issue: item.json.issue, filename: name,
        content_type: file.mimeType || 'application/octet-stream' },
      binary: { data: file },
      pairedItem: { item: group },
    });
  }
}
return output;
