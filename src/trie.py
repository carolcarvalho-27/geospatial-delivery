
class _Node:
    """Nó interno da Trie compacta."""

    def __init__(self):
        self.children = {}
        self.values = []


class Trie:
    """Trie compacta para associar chaves textuais a valores."""

    def __init__(self):
        self.root = _Node()

    @staticmethod
    def _common_prefix_length(first: str, second: str) -> int:
        """Retorna o tamanho do prefixo comum entre duas strings."""
        limit = min(len(first), len(second))
        i = 0

        while i < limit and first[i] == second[i]:
            i += 1

        return i

    def insert(self, key: str, value) -> None:
        """Insere um valor associado a uma chave não vazia."""
        if not isinstance(key, str) or not key:
            raise ValueError("A chave deve ser uma string não vazia.")

        self._insert(self.root, key, value)

    def _insert(self, node: _Node, key: str, value) -> None:
        for edge, child in list(node.children.items()):
            common = self._common_prefix_length(key, edge)

            if common == 0:
                continue

            if common == len(edge):
                remainder = key[common:]

                if remainder:
                    self._insert(child, remainder, value)
                elif value not in child.values:
                    child.values.append(value)

                return

            # A chave e a aresta compartilham apenas parte do prefixo.
            old_suffix = edge[common:]
            middle = _Node()

            del node.children[edge]
            node.children[edge[:common]] = middle
            middle.children[old_suffix] = child

            new_suffix = key[common:]

            if new_suffix:
                middle.children[new_suffix] = _Node()
                middle.children[new_suffix].values.append(value)
            elif value not in middle.values:
                middle.values.append(value)

            return

        # Nenhuma aresta existente compartilha o início da chave.
        new_node = _Node()
        new_node.values.append(value)
        node.children[key] = new_node

    def search_prefix(self, prefix: str) -> list:
        """Retorna os valores associados a chaves iniciadas pelo prefixo."""
        if not isinstance(prefix, str):
            raise ValueError("O prefixo deve ser uma string.")

        node = self.root
        remainder = prefix

        if not remainder:
            return self._collect_values(node)

        while remainder:
            found = False

            for edge, child in node.children.items():
                common = self._common_prefix_length(remainder, edge)

                if common == 0:
                    continue

                # O prefixo terminou, inclusive no meio de uma aresta.
                if common == len(remainder):
                    return self._collect_values(child)

                # A aresta inteira foi percorrida.
                if common == len(edge):
                    node = child
                    remainder = remainder[common:]
                    found = True
                    break

            if not found:
                return []

        return self._collect_values(node)

    def _collect_values(self, node: _Node) -> list:
        """Percorre uma subárvore e reúne todos os valores."""
        result = list(node.values)

        for child in node.children.values():
            result.extend(self._collect_values(child))

        return result

    def remove(self, key: str, value) -> bool:
        """Remove um valor de uma chave. Retorna True se o removeu."""
        if not isinstance(key, str) or not key:
            raise ValueError("A chave deve ser uma string não vazia.")

        return self._remove(self.root, key, value)

    def _remove(self, node: _Node, key: str, value) -> bool:
        for edge, child in list(node.children.items()):
            if not key.startswith(edge):
                continue

            remainder = key[len(edge):]

            if remainder:
                removed = self._remove(child, remainder, value)
            else:
                if value not in child.values:
                    return False

                child.values.remove(value)
                removed = True

            if not removed:
                return False

            # Remove nós vazios e compacta caminhos sem ramificações.
            if not child.values and not child.children:
                del node.children[edge]
            elif not child.values and len(child.children) == 1:
                next_edge, grandchild = next(iter(child.children.items()))
                del node.children[edge]
                node.children[edge + next_edge] = grandchild

            return True

        return False
